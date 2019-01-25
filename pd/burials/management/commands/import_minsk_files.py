# coding=utf-8

# import_minsk_files.py
#
# Запуск (например): ./manage.py import_minsk_files ofiles 2 Восточное Уручье
#
# где:
#
#   ofiles:             каталог в settings.MEDIA_ROOT, куда положили
#                       файлы из каталога ofiles Минской набивалки.
#                       После отработки процедуры каталог ofiles можно
#                       и нужно удалить
#
#   2:                  ID ОМС, в захоронения которого импортируем файлы
#
#   Восточное Уручье:   Одно или несколько названий кладбищ, в захоронения
#                       которых импортируем файлы

import os, shutil, re, pytils

from django.conf import settings
from django.core.management.base import BaseCommand

from users.models import Org
from burials.models import Cemetery, Burial, BurialFiles

class Command(BaseCommand):
    help = "Fill media/bfiles with files from Minsk bunch of cemeteries"

    def add_arguments(self, parser):
        parser.add_argument('ofiles_path', type=str)

    def handle(self, *args, **kwargs):
        error = u'!!! Error'
        warning = u'*** Warining'
        ofiles=kwargs['ofiles_path']
        media_root = re.sub(r'/+$', '', settings.MEDIA_ROOT)
        ofiles = re.sub(r'/+$', '', os.path.join(media_root, ofiles))
        if not os.path.isdir(ofiles):
            print u"%s. Not found ofiles folder: %s" % (error, ofiles)
            quit()
        try:
            ugh_pk=args[1]
        except IndexError:
            print u"%s. No oms_pk given" % error
            quit()
        try:
            ugh = Org.objects.get(pk=ugh_pk, type=Org.PROFILE_UGH)
        except (Org.DoesNotExist, ValueError,):
            print u"%s. OMS with pk=%s not found" % (error, ugh_pk)
            quit()
        cemeteries = list()
        for cemetery_name in args[2:]:
            cemetery_name = cemetery_name.decode("utf-8")
            try:
                cemeteries.append(Cemetery.objects.get(ugh=ugh, name=cemetery_name))
            except Cemetery.DoesNotExist:
                print u"%s. Cemetery '%s' not found at OMS with pk=%s" % (error, cemetery_name, ugh_pk)
                quit()
        if not cemeteries:
            print u"%s. Cemetery_name list is empty" % (error, )
            quit()
        burial_files = BurialFiles.objects.filter(burial__cemetery__in=cemeteries, bfile__gt=u'')
        if not burial_files.exists():
            print u"%s. No burial files for this bundle of cemeteries." % (warning, )
            quit()
        regex = re.compile(r'^bfiles/\d{4,}/\d{2}/\d{2}/(\d+)/[^/]+$')
        for bf in burial_files:
            bf_name = unicode(bf.bfile)
            match = re.search(regex, bf_name)
            if not match:
                print "%s. File: %s does not correspond to a burial file template" % (error, bf_name)
                quit()
            burial_pk = match.group(1)
            try:
                burial = Burial.objects.get(pk=burial_pk, ugh=ugh, cemetery__in=cemeteries)
            except (Burial.DoesNotExist, ValueError,):
                print "%s. File: %s does not correspond to OMS, pk=%s, or to the cemeteries specified" % (error, bf_name, ugh_pk,)
                quit()
        count = count_absent = count_slugified = count_overwritten = 0
        for bf in burial_files:
            bf_name = unicode(bf.bfile)
            fname = re.sub(r'^.+/([^/]+)$', r'\1', bf_name)
            src_file = os.path.join(ofiles, fname)
            if not os.path.isfile(src_file):
                print "%s. File: %s does not exist" % (warning, src_file)
                count_absent += 1
                continue
            dest_dir = os.path.join(settings.MEDIA_ROOT, re.sub(r'^(.+)/[^/]+$', r'\1', bf_name))
            if not os.path.isdir(dest_dir):
                try:
                    os.makedirs(dest_dir)
                except OSError:
                    print "%s. Failed to create folder: %s" % (error, dest_dir,)
                    quit()
            dest_fname = u'.'.join(map(pytils.translit.slugify, fname.rsplit('.', 1)))
            new_bf_name = re.sub(r'%s$' % re.escape(fname), dest_fname, bf_name)
            dest_file = os.path.join(dest_dir, dest_fname)
            # print src_file, "\n", new_bf_name, "\n", dest_file, "\n"
            if os.path.isfile(dest_file):
                print "%s. File: %s is to be overwritten" % (warning, dest_file)
                count_overwritten += 1
            shutil.copy2(src_file, dest_file)
            if bf_name != new_bf_name:
                bf.bfile = new_bf_name
                bf.save()
                count_slugified += 1
            count += 1
        print "*** %s burial files imported,\n" \
              "    %s of them slugified.\n" \
              "    %s of them OVERWRITTEN!\n" \
              "    %s burial files NOT FOUND!\n" % (
            count,
            count_slugified,
            count_overwritten,
            count_absent,
        )
        print "*** DO NOT FORGET to remove %s folder. It is of no further use from now on" % (
            ofiles,
        )
