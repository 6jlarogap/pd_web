from django_assets import Bundle, register

js_app = Bundle(
        "js/app/const.js",
        "js/app/app.lib.js",
        "js/app/app.js",
        "js/app/app.config.js",
        "js/app/app.filter.js",

        "js/app/resources/address.js",
        "js/app/resources/place.js",
        "js/app/resources/cemetery.js",
        "js/app/resources/grave.js",
        "js/app/resources/burial.js",
        "js/app/resources/area.js",
        "js/app/resources/area_purpose.js",
        "js/app/resources/area_photo.js",
        "js/app/resources/person.js",
        "js/app/resources/phone.js",
        "js/app/resources/log.js",
        "js/app/resources/placesize.js",
    
        "js/app/directive/address/address.js",
        "js/app/directive/phones/phones.js",
        "js/app/directive/google.js",
        
        "js/app/filter/natural_sort.js",
    
        #"angular-ui-bootstrap/src/dialog/dialog.js",
    
        "js/app/directive/angular-ymaps.js",
        
        "js/app/controller/cemetery.js",
        "js/app/controller/cemetery_view.js",
        "js/app/controller/area_view.js",
        "js/app/controller/place_view.js",
        "js/app/controller/support_view.js",

        "js/app/directive/file_upload.js",
        filters='rjsmin', output='pd.js')
    

js_angular = Bundle(
        #<script type="text/javascript" src="{% static 'angular/angular.min.js' %}"></script>
        "ng-grid/ng-grid-2.0.7.debug.js",

        # "angular/angular.min.js",
        # "js/angular/angular-bootstrap.js",
        # "js/angular/i18n/angular-locale_ru-ru.js",

        "js/jquery/vendor/jquery.ui.widget.js",
    
        "angular-resource/angular-resource.min.js",
        "angular-cookies/angular-cookies.min.js",

        "angular-bootstrap/ui-bootstrap.min.js",
        "angular-bootstrap/ui-bootstrap-tpls.min.js",

        "angular-ui-utils/modules/mask/mask.js",
        "angular-ui-utils/modules/validate/validate.js",

        "select2/select2.min.js",
        "select2/select2_locale_ru.js",

        "momentjs/moment.js",
        #"ng-grid/ng-grid-2.0.7.debug.js",
    
        "js/bootstrap-typeahead.js",
        
        #"js/angular3d/bootstrap-typeahead.js",
        "lodash/dist/lodash.compat.min.js",

        "js/bootstrap-typeahead.js",
        #"ng-grid/ng-grid/src/i18n/ru.js",

        "js/angular3d/modules/jquery.fileupload-angular.js",

        filters='rjsmin', output='pd-angular.js')





js_fileupload = Bundle(
        "js/jquery/fileupload/jquery.iframe-transport.js",
        "js/jquery/fileupload/jquery.fileupload.js",
        "js/jquery/fileupload/jquery.fileupload-process.js",
        "js/jquery/fileupload/jquery.fileupload-image.js",
        "js/jquery/fileupload/jquery.fileupload-audio.js",
        "js/jquery/fileupload/jquery.fileupload-video.js",
        "js/jquery/fileupload/jquery.fileupload-validate.js",
        filters='rjsmin', output='pd-fu.js')


js_jquery = Bundle(
        "jquery-ui/ui/minified/jquery-ui.min.js",
        "jquery-ui/ui/minified/jquery.ui.datepicker.min.js",
        "jquery-ui/ui/minified/i18n/jquery.ui.datepicker-ru.min.js",
        "jquery-timepicker/jquery.ui.timepicker.js",
        
        "noty/js/noty/jquery.noty.js",
        "noty/js/noty/layouts/topRight.js",
        "noty/js/noty/themes/default.js",
        filters='rjsmin', output='pd-jq.js')


js_bootstrap_static = Bundle(
        "js/bootstrap-dropdown.js",
        "js/bootstrap-modal.js",
        "js/bootstrap-typeahead-ajax.js",
        filters='rjsmin', output='pd-static.js')


css_app = Bundle(
        "js/jquery/fileupload/jquery.fileupload-ui.css",
        "select2/select2.css",
        "ng-grid/ng-grid.min.css",
        "js/app/app.css",
        filters='cssmin', output='pd.css')


css_static = Bundle(
        "css/base.css",
        filters='cssmin', output='pd-static.css')


css_print = Bundle(
        "css/print.css",
        filters='cssmin', output='pd-print.css')


register('js_app', js_app)
register('js_angular', js_angular)
register('js_fileupload', js_fileupload)
register('js_jquery', js_jquery)
register('js_bootstrap_static', js_bootstrap_static)

register('css_app', css_app)
register('css_static', css_static)
register('css_print', css_print)
