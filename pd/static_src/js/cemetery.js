/**
 * Created with PyCharm.
 * User: ilvar
 * Date: 06.06.12
 * Time: 23:30
 * To change this template use File | Settings | File Templates.
 */

function setup_address_autocompletes() {
    if (top.location.href != '/') {
        if (navigator.userAgent.toLowerCase().indexOf("chrome") >= 0) {
            $('input:-webkit-autofill').each(function(){
                var text = $(this).val();
                var name = $(this).attr('name');
                $(this).after(this.outerHTML).remove();
                $('input[name=' + name + ']').val(text);
            });
        }
    }
    $('.burial-form input').attr('autocomplete', 'off');

    COUNTRY_URL = '/geo/autocomplete/country/';
    REGION_URL = '/geo/autocomplete/region/';
    CITY_URL = '/geo/autocomplete/city/';
    STREET_URL = '/geo/autocomplete/street/';
    DOCS_SOURCE_URL = '/autocomplete/doc_source/';
    FIO_URL = '/autocomplete/fio/';
    CEMETERIES_URL = '/autocomplete/cemeteries/';
    AREAS_URL = '/autocomplete/areas/';
    ALIVE_FIO_URL = '/autocomplete/alive/';
    FIRST_NAME_URL = '/autocomplete/firstname/';
    MIDDLE_NAME_URL = '/autocomplete/middlename/';
    ORG_URL = '/autocomplete/org/';
    DOCSOURCE_URL = '/autocomplete/docsources/';


    $('#id_instance_0').live('click', function(){
        var form = $(this).parents('.well');
        form.find('.instance_alert').remove();
        form.prepend('<p class="instance_alert alert">Очистите поля ФИО для нового поиска</p>')
    });

    $('#id_applicant-pid-source').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: DOCSOURCE_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('select[name*=fias_]').each(function() {
        if (!$(this).children('option[value!=""]').length) {
            $(this).closest('p').hide();
        }
    });

    $('#mainform #id_applicant_org').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: ORG_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('input[id$=zags]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: ORG_URL + "?query=" + query + "&type=zags",
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('#mainform #id_applicant_person, #mainform #id_responsible').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: ALIVE_FIO_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('#mainform #id_cemetery').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: CEMETERIES_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('#mainform #id_area').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 1) { return }
            var input = $(this)[0].$element;
            var cem = input.parents('#mainform').find('#id_cemetery').val() || '';
            $.ajax({
                url: AREAS_URL + "?query=" + query + '&cemetery=' + cem,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });



    $('#id_fio').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: FIO_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('#id_applicant-first_name, #id_deadman-first_name, #id_responsible-first_name').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: FIRST_NAME_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('#id_applicant-middle_name, #id_deadman-middle_name, #id_responsible-middle_name').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: MIDDLE_NAME_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('input[name$=country_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: COUNTRY_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });

    $('input[name$=region_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            var input = $(this)[0].$element;
            typeahead.input_el = input;
            var country = input.parents('.form_block').find('input[name$=country_name]').val() || '';
            $.ajax({
                url: REGION_URL + "?query=" + query + "&country=" + country,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        },
        onselect: function(val) {
            var $country = $(this)[0].$element.closest('form,.form_block').find('input[name$=country_name]');
            if (!$country.val()) {
                $country.val(val.country);
            };
            this.$element.val(val.real_value);
        }
    });
    $('input[name$=city_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            var input = $(this)[0].$element;
            var region = input.parents('.form_block').find('input[name$=region_name]').val() || '';
            var country = input.parents('.form_block').find('input[name$=country_name]').val() || '';
            $.ajax({
                url: CITY_URL + "?query=" + query + "&country=" + country + "&region=" + region,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        },
        onselect: function(val) {
            var $region = $(this)[0].$element.closest('form,.form_block').find('input[name$=region_name]');
            if (!$region.val()) {
                $region.val(val.region);
            }
            var $country = $(this)[0].$element.closest('form,.form_block').find('input[name$=country_name]');
            if (!$country.val()) {
                $country.val(val.country);
            }
            this.$element.val(val.real_value);
        }
    });
    $('input[name$=street_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            var input = $(this)[0].$element;
            var country = input.parents('.form_block').find('input[name$=country_name]').val() || '';
            var region = input.parents('.form_block').find('input[name$=region_name]').val() || '';
            var city = input.parents('.form_block').find('input[name$=city_name]').val() || '';
            $.ajax({
                url: STREET_URL + "?query=" + query + "&country=" + country + "&region=" + region + "&city=" + city,
                dataType: 'json',
                success: function(data) {
                    typeahead.saved_geo_data = data;
                    typeahead.process(data);
                }
            });
        },
        onselect: function(val) {
            var $city = $(this)[0].$element.closest('form,.form_block').find('input[name$=city_name]');
            if (!$city.val()) {
                $city.val(val.city);
            }
            var $region = $(this)[0].$element.closest('form,.form_block').find('input[name$=region_name]');
            if (!$region.val()) {
                $region.val(val.region);
            }
            var $country = $(this)[0].$element.closest('form,.form_block').find('input[name$=country_name]');
            if (!$country.val()) {
                $country.val(val.country);
            }
            $(this)[0].$element.val(val.street);
        }
    });
    $('#id_customer_id-source').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            $.ajax({
                url: DOCS_SOURCE_URL + "?query=" + query,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        }
    });
}

function updateAnything(parent, children, data) {
    var cem = parent.val();
    var val = children.val();
    var options = '<option value="">----------</option>';
    var area_list = data[cem] || [];
    for (var i in area_list) {
        options += '<option value="'+area_list[i][0]+'">'+area_list[i][1]+'</option>';
    }
    children.html(options);
    if (val) {
        children.val(val);
    }
    children.change();
}

function updateAreas() {
    updateAnything($('#id_cemetery'), $('#id_area'), CEMETERY_AREAS);
}

function updateDover() {
    updateAnything($('#id_agent'), $('#id_dover'), AGENT_DOVER);
    if (!$('#id_dover').val()) {
        // Когда пользователь прыгает от одного агента к другому,
        // ему предлагается из доверенностей соответствующего агента
        // последняя из актуальных. Это нельзя делать при
        // загрузке страницы зх (заказа...), в котором уже
        // есть агент и доверенность, т.е. где в выпадающем
        // списке доверенностей есть уже выбранное значение
        $('#id_dover').find('option').each(function() {
            if (ACTUAL_DOVER.indexOf(parseInt(this.value)) > -1) {
                this.selected = 'selected';
            }
        });
    }
}

function updateAgents() {
    updateAnything($('#id_applicant_organization'), $('#id_agent'), ORG_AGENTS);
}

function updateTimes() {
    var val = $('#id_plan_time').val();
    $('input#id_plan_time').replaceWith('<select id="id_plan_time" name="plan_time"></select>');
    updateAnything($('#id_cemetery'), $('#id_plan_time'), CEMETERY_TIMES);
    if ($('select#id_plan_time option').length < 2) {
        $('select#id_plan_time').replaceWith('<input type="text" id="id_plan_time" name="plan_time"></input>');
        $('#id_plan_time').closest('p').find('.add-on').remove();
        makeTimePicker($('#id_plan_time'));
    }
    $('#id_plan_time').val(val);
}

$(function() {
    updateControls();

    if (!window.CEMETERY_AREAS) { CEMETERY_AREAS = {} }
    if (!window.CEMETERY_TIMES) { CEMETERY_TIMES = {} }
    if (!window.AGENT_DOVER) { AGENT_DOVER = {} }
    if (!window.ORG_AGENTS) { ORG_AGENTS = {} }
    if (!window.PLACE_TYPES) { PLACE_TYPES = {} }
    if (!window.PLACE_SIZE) { PLACE_SIZE = {} }
    
    $('input[id$=fias_address]').live('keypress', function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
            $(this).change();
            return false;
        }
    });

    $('.burial-form, .order_form').find(':input').live('keypress', function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
            $(this).change();
            return false;
        }
    });

    $('input[name$=last_name], input[name$=first_name], input[name$=middle_name]').parents('p').addClass('inline');

    $('.burial-form,.order_form, .main-form').find(':input').live('blur', function(e) {
        $(this).change();
    });

    var SOMETHING_CHANGED = false
    $('.main-form :input').change(function() {
        SOMETHING_CHANGED = true;
    });
    $('.add-row, .delete-row').click(function() {
        SOMETHING_CHANGED = true;
    });

    $('.main-form .btn-next').click(function() {
        if (SOMETHING_CHANGED) {
            return confirm('Есть несохраненные изменения. Действительно уйти?')
        } else {
            return true;
        }
    });

    $('.btn-commit-burial').click(function() {
        if ($(this).attr('rel')) {
            $(this).closest('form').attr('action', $(this).attr('rel'));
        }
    });

    $('#id_cemetery').change(updateAreas);
    updateAreas();

    $('#id_cemetery').change(updateTimes);
    updateTimes();

    $('#id_agent').change(updateDover);
    $('#id_agent').change(function() {
        if ($(this).val()) {
            $('.btn-dover').closest('p').show();
        } else {
            $('.btn-dover').closest('p').hide();
        }
    });
    $('#id_agent:visible').change();

    $('#id_applicant_organization').change(updateAgents);
    $('#id_applicant_organization').change(function() {
        if (!$('#id_agent_director').is(':checked')) {
            if ($(this).val()) {
                $('.btn-agent').closest('p').show();
            } else {
                $('.btn-agent').closest('p').hide();
            }
        }
    });
    $('#id_applicant_organization:visible').change();

    $('#id_plan_date, #id_cemetery').change(function() {
        var cem = $('#id_cemetery').val();
        var date = $('#id_plan_date').val();
        if (cem && date) {
            $.getJSON('/cemetery_times/?cem='+cem+'&date='+date, function(data) {
                CEMETERY_TIMES = data;
                updateTimes();
            });
        } else {
            CEMETERY_TIMES = {};
            updateTimes();
        }
    });
    $('#id_plan_date').change();

    old_zags_value = '';
    
    $('input[id$=zags]').change(function() {
        var zags_inp =$(this);
        var val = zags_inp.val();
        if (val != '' && val != old_zags_value) {
            // загадка, почему дважды приходит событие change,
            // оба раза с одним неверным значением,
            // хотя ниже оно затирается
            old_zags_value = val;
            $.ajax({
                url: ORG_URL + "?query=" + val + "&type=zags&exact=1",
                dataType: 'json',
                success: function(data) {
                    if (data.length == 0) {
                        alert("Нет такого ЗАГСа");
                        zags_inp.val('');
                        old_zags_value = '';
                    }
                }
            });
        }
    });

    $('input[name=opf]').change(function() {
        var resp_id = '#id_responsible-take_from_';
        $(resp_id+'1').removeAttr('checked').closest('li').hide();
        var new_order = top.location.href.toLowerCase().indexOf('/order/create') != -1
        if ($('input[name=opf]:checked').val() == 'org') {
            $('#applicant_form_org').show();
            $('#applicant_form_person').hide();

            $('#id_applicant_organization').closest('p').show();
            $('#id_agent_director').closest('p').show();
            $('#id_applicant_organization').change();

            $('input[name^=person]').closest('p').hide();
            $('#id_org').closest('p').show();

            $('.btn-loru').closest('p').show();
            $('.btn-org').closest('p').show();

            $('#id_agent_director').change();
            if (new_order) {
                $('input[name=payment][value=wire]').attr('checked', '1');
            }
        }
        else if ($('input[name=opf]:checked').val() == 'person') {
            $('#applicant_form_org').hide();
            $('#applicant_form_person').show();

            $('#id_applicant_organization').closest('p').hide();
            $('#id_agent_director').closest('p').hide();
            $('#id_agent').closest('p').hide();
            $('#id_dover').closest('p').hide();

            $('.btn-loru').closest('p').hide();
            $('.btn-dover').closest('p').hide();
            $('.btn-agent').closest('p').hide();
            $('.btn-org').closest('p').hide();

            $('input[name^=person]').closest('p').show();
            $('#id_org').closest('p').hide();
            if (new_order) {
                $('input[name=payment][value=cash]').attr('checked', '1');
            }

            $(resp_id+'1').closest('li').show();
            if (!$(resp_id+'0').is(':checked') && !$(resp_id+'2').is(':checked')) {
                $(resp_id+'1').attr('checked', 'checked');
            }
        }
        else if ($('input[name=opf]:checked').val() == 'empty') {
            $('#applicant_form_org').hide();
            $('#applicant_form_person').hide();

            $('#id_applicant_organization').closest('p').hide();
            $('#id_agent_director').closest('p').hide();
            $('#id_agent').closest('p').hide();
            $('#id_dover').closest('p').hide();

            $('.btn-loru').closest('p').hide();
            $('.btn-dover').closest('p').hide();
            $('.btn-agent').closest('p').hide();
            $('.btn-org').closest('p').hide();

            $('input[name^=person]').closest('p').hide();
            $('#id_org').closest('p').hide();
        }
    });
    $('input[name=opf]').change();

    $('input[name=nb_choice]').change(function() {
        if ($('input[name=nb_choice]:checked').val() == 'new') {
            $('input[name=nb_burial]').closest('p').hide();
        } else {
            $('input[name=nb_burial]').closest('p').show();
        }
    });
    $('input[name=nb_choice]').change();

    $('form.burial-form :input:visible:first').focus();

    $('#id_agent_director').change(function() {
        if ($(this).is(':checked')) {
            $('#id_dover').closest('div').hide();
            $('#id_agent').closest('div').hide();
        } else {
            $('#id_dover').closest('div').show();
            $('#id_agent').closest('div').show();
            $('#id_applicant_organization').change();
        }
    });
    $('#id_agent_director:visible').change();

    $('#add_agent').find('.btn-primary').click(function() {
        var org_pk = $('#id_applicant_organization').val();
        if (!org_pk) {
            return alert('Выберите организацию');
        }
        var data = $('#add_agent form').serialize();
        $.post('/burials/add_agent/?org='+org_pk, data, function(data){
            if (data.pk) {
                $('#id_agent').append('<option value="'+data.pk+'">'+data.label+'</option>');
                $('#id_dover').append('<option value="'+data.dover_pk+'">'+data.dover_label+'</option>');
                $('#id_agent').val(data.pk);
                $('#id_dover').val(data.dover_pk);
                if (!ORG_AGENTS[org_pk]) {
                    ORG_AGENTS[org_pk] = [];
                }
                ORG_AGENTS[org_pk].push([data.pk, data.label])
                if (!AGENT_DOVER[data.pk]) {
                    AGENT_DOVER[data.pk] = [];
                }
                AGENT_DOVER[data.pk].push([data.dover_pk, data.dover_label])
                $('#add_agent').modal('hide');
                $('#add_agent form :input').val('');
            } else {
                alert(data);
            }
        })
    });

    $('#add_doctype').find('.btn-primary').click(function() {
        var data = $('#add_doctype form').serialize();
        $.post('/burials/add_doctype/', data, function(data){
            if (data.pk) {
                $('#id_applicant-pid-id_type').append('<option value="'+data.pk+'">'+data.label+'</option>');
                $('#id_applicant-pid-id_type').val(data.pk);
                $('#add_doctype').modal('hide');
                $('#add_doctype form :input').val('');
            } else {
                alert(data);
            }
        })
    });

    $('#add_dover').find('.btn-primary').click(function() {
        var agent_pk = $('#id_agent').val();
        if (!agent_pk) {
            return alert('Выберите агента');
        }
        var data = $('#add_dover form').serialize();
        $.post('/burials/add_dover/?agent='+agent_pk, data, function(data){
            if (data.pk) {
                $('#id_dover').append('<option value="'+data.pk+'">'+data.label+'</option>');
                $('#id_dover').val(data.pk);
                if (!AGENT_DOVER[agent_pk]) {
                    AGENT_DOVER[agent_pk] = [];
                }
                AGENT_DOVER[agent_pk].push([data.pk, data.label])
                $('#add_dover').modal('hide');
                $('#add_dover form :input').val('');
            } else {
                alert(data);
            }
        })
    });

    $('#add_loru').find('.btn-primary').click(function() {
        var data = $('#add_loru form').serialize();
        //TODO validation on client!
        $.post('/burials/add_org/', data, function(data){
            if (data.pk) {
                ORGS_INACTIVE.push(data.pk.toString())
                var select = $('#id_applicant_organization');
                select.append('<option value="'+data.pk+'" selected="selected">'+data.label+'</option>');
                select.val(data.pk);
                $('#add_loru').modal('hide');
                $('#add_loru form :input').val('');
                $("#applicant_form_org div.inline input").val(data.label);
                $("#applicant_form_org div.inline input").data('typeahead').source.push(data.label);
                select.change();
            } else {
                alert(data);
            }
        })
    });

    $('#add_zags').find('.btn-primary').click(function() {
        var data = $('#add_zags form').serialize();
        $.post('/burials/add_zags/', data, function(data){
            if (data.pk) {
                if (typeof ORGS_INACTIVE != "undefined") {
                    ORGS_INACTIVE.push(data.pk.toString());
                    ORGS_LIST.push(data.label);
                    var select = $('#id_applicant_organization');
                    select.append('<option value="'+data.pk+'" selected="selected">'+data.label+'</option>');
                }
                $('#add_zags').modal('hide');
                $('#id_deadman-dc-zags').val(data.label);
            } else {
                alert(data);
            }
        })
    });

    old_grave_value = $('#id_grave_number').val();

    $('#cont_place #id_cemetery, #cont_place #id_area, #cont_place #id_row, #cont_place #id_place_number, #id_desired_graves_count').change(function() {
        $('#id_responsible-take_from_0').removeAttr('checked').closest('li').hide();

        var data = $('#id_cemetery, #id_area, #id_row, #id_place_number, #id_desired_graves_count').serialize();
        if ($('#id_cemetery').val() &&  $('#id_area').val() && $('#id_place_number').val()) {
            // $('#place_info').load('/burials/get_place/?'+data)
            $.get('/burials/get_place/?'+data, function (data) {
                var place_html = data;
                $('#place_info').html(place_html);
                if (place_html.indexOf("place_exists") >= 0) {
                    $('#id_desired_graves_count').closest('p').hide();
                    if ($('#id_place_length').length > 0) {
                        $('#id_place_length').closest('p').hide();
                        $('#id_place_width').closest('p').hide();
                    }
                }
                else {
                    $('#id_desired_graves_count').closest('p').show();
                    if ($('#id_place_length').length > 0) {
                        $('#id_place_length').closest('p').show();
                        $('#id_place_width').closest('p').show();
                    }
                }
                if (place_html.indexOf("place_has_responsible") >= 0) {
                    var resp_id = '#id_responsible-take_from_';
                    $(resp_id+'0').closest('li').show();
                    // 0 - из места
                    // 1 - заявитель
                    // 2 - новый ответственный
                    if (!$(resp_id+'1').is(':checked') && !$(resp_id+'2').is(':checked')) {
                        $(resp_id+'0').attr('checked', 'checked');
                    }
                }
            });
        } else {
            $('#id_desired_graves_count').closest('p').show();
            if ($('#id_place_length').length > 0) {
                $('#id_place_length').closest('p').show();
                $('#id_place_width').closest('p').show();
            }
            $('#place_info').html('');
        }

        $.getJSON('/burials/get_graves_number/?'+data, function(data) {
            var count = data.graves_count || 1;
            count = Math.max(parseInt(old_grave_value), count);
            if (count != $('#id_grave_number').find('option').length) {
                var options = '';
                for (var i=1; i<=count; i++) {
                    var selected = i == old_grave_value ? ' selected="selected"' : '';
                    options += '<option value="'+i+'"'+selected+'>'+i+'</option>';
                }
                $('#id_grave_number').html(options);
            }
            $('#id_responsible-place').val(data.place_pk || "");
        })
        var cemetery = $('#id_cemetery').val();
        if (cemetery && PLACE_TYPES[cemetery] != 'manual') {
            $('#id_place_number').siblings('.helptext').show();
        } else {
            $('#id_place_number').siblings('.helptext').hide();
        }
    });
    $('#id_cemetery, #id_area, #id_row, #id_place_number').change();

    $('input[name=responsible-take_from]').change(function() {
        if ($('input[name=responsible-take_from]:checked').val() == 'new') {
            $('input[name^=responsible-]:not([name=responsible-take_from])').closest('p').show();
            $('#cont_responsible_address').show();
        } else {
            $('input[name^=responsible-]:not([name=responsible-take_from])').closest('p').hide();
            $('#cont_responsible_address').hide();
        }
    });
    $('input[name=responsible-take_from]').change();


    $('#id_grave_number').change(function() {
        old_grave_value = $('#id_grave_number').val();
    });

    $('#id_desired_graves_count, #id_new_graves_count').change(function() {
        var size = PLACE_SIZE[$(this).val()] || '';
        if (size) {
            $('#id_place_length').val(size['place_length']);
            $('#id_place_width').val(size['place_width']);
        } else {
            $('#id_place_length').val('');
            $('#id_place_width').val('');
        }
    });

    $('#id_country, #id_region').change(function() {
        var geocoder = new google.maps.Geocoder();
        var addr = $('#id_country [selected]').text() + ', ' + $('#id_region [selected]').text();
        geocoder.geocode( { 'address': addr}, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                $('#id_lat').val(results[0].geometry.location.lat());
                $('#id_lng').val(results[0].geometry.location.lng());
            }
        });
    });
    $('#id_country, #id_region').change();
    $('#id_lat, #id_lng').closest('p').hide();

    $('#id_org-name, #id_zags-name, #id_org_name').change(function() {
        var val = $(this).val();
        var full_name = "";
        switch ($(this).attr('id')) {
            case 'id_org-name':
                full_name = '#id_org-full_name';
                break;
            case 'id_zags-name':
                full_name = '#id_zags-full_name';
                break;
            case 'id_org_name':
                full_name = '#id_org_full_name';
                break;
        }
        if (val && !$(full_name).val()) {
            $(full_name).val(val);
        }
    });

    var ac_options = {
        bounds: USER_DEFAULT_BOUNDS,
        types: ['geocode'],
        componentRestrictions: {country: 'ru'}
    };
    $('input[id$=fias_address]').attr('autocomplete', 'off').css('width', '600px').each(function() {
        var autocomplete = new google.maps.places.Autocomplete(this, ac_options );
        var $input = $(this);
        google.maps.event.addListener(autocomplete, 'place_changed', function () {
            $input.change();
        });
    });
    $('.modal-body input[id$=fias_address]').css('width', '300px');

    $('input[id$=fias_address]').change(function() {
        var street_input = $('input[id$=fias_street]');
        street_input.val('');
        var addr_input = $(this);
        var form_block = addr_input.closest('.form_block');
        form_block.find('#fias_street_info').hide();
        var addr = $(this).val();
        if (!addr) { return }

        var geocoder = new google.maps.Geocoder();
        geocoder.geocode( { 'address': addr, 'language': 'ru' }, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                var country = '', region = '', city = '', street = '';
                var house = '', building = '', block = '', flat = '';
                form_block.find('[id$=post_index], [id$=country_name], [id$=region_name], [id$=city_name]').val('');
                form_block.find('[id$=street_name]').val('');

                var address = results[0].address_components;
                $(address).each(function() {
//                     if (this.types.indexOf("postal_code") > -1) { form_block.find('input[id$=post_index]').val(this.long_name); }
                    if (this.types.indexOf("country") > -1) { country = this.long_name; form_block.find('input[id$=country_name]').val(country); }
                    if (this.types.indexOf("administrative_area_level_1") > -1) { region = this.long_name; form_block.find('input[id$=region_name]').val(''); }
                    if (this.types.indexOf("locality") > -1) { city = this.long_name; form_block.find('input[id$=city_name]').val(''); }
                    if (this.types.indexOf("route") > -1) { street = this.long_name; form_block.find('input[id$=street_name]').val(''); }
//                     if (this.types.indexOf("street_number") > -1) {
//                         form_block.find('input[id$=house]').val(this.long_name);
//                         house = this.long_name;
//                         if (this.long_name.indexOf("корпус") > -1) {
//                             var bits = this.long_name.split(" корпус ");
//                             form_block.find('input[id$=house]').val(bits[0]);
//                             form_block.find('input[id$=block]').val(bits[1]);
//                             house = bits[0];
//                             block = bits[1];
//                         }
//                         if (this.long_name.indexOf("строение") > -1) {
//                             var bits = this.long_name.split(" строение ");
//                             form_block.find('input[id$=house]').val(bits[0]);
//                             form_block.find('input[id$=building]').val(bits[1]);
//                             house = bits[0];
//                             building = bits[1];
//                         }
//                     }
//                     if (this.types.indexOf("subpremise") > -1) {
//                         flat = this.long_name;
//                         form_block.find('input[id$=flat]').val(this.long_name);
//                     }
                });

                if (country) {
                    form_block.find('input[id$=region_name]').val(region);
                    form_block.find('input[id$=city_name]').val(city);
                    form_block.find('input[id$=street_name]').val(street);
                }
            } else {
                alert("Ошибка адреса, status="+status)
            }
        })
    });
    // Начальная загрузка страницы. Не делаем change, иначе загонит в страну, ..., улицу
    // то, что найдет по содержимому строки поиска по адресу. А заодно затираем.
    // Нужен будет новый поиск, начнет с "чистого листа".
    // $('input[id$=fias_address]').change();
    $('input[id$=fias_address]').val('');

    $('#paginator_select').live('change', function() {
        top.location.href = $(this).val();
    });

    $('input.autocomplete[name$=city_name]').live('change', function() {
        $(this).closest('.well').find('input.autocomplete[name$=street_name]').val('');
    });

    $('input.autocomplete[name$=region_name]').live('change', function() {
        $(this).closest('.well').find('input.autocomplete[name$=street_name]').val('');
        $(this).closest('.well').find('input.autocomplete[name$=city_name]').val('');
    });

    $('input.autocomplete[name$=country_name]').live('change', function() {
        $(this).closest('.well').find('input.autocomplete[name$=street_name]').val('');
        $(this).closest('.well').find('input.autocomplete[name$=city_name]').val('');
        $(this).closest('.well').find('input.autocomplete[name$=region_name]').val('');
    });

    $('.errorlist').addClass('alert');

    $('.dropdown-toggle').dropdown();
});

function makeDatePicker(obj) {
    $.datepicker.setDefaults($.datepicker.regional['']);
    var now = new Date();
    var now_year = now.getFullYear();

    obj.after('<span class="add-on move-left"><i class="icon-calendar"></i></span>').datepicker({
        dateFormat: 'dd.mm.yy',
        changeMonth: true,
        changeYear: true,
        yearRange: '1900:' + now_year,
        firstDay: 1,
        monthNamesShort: ['Янв','Фев','Март','Апрель','Май','Июнь','Июль','Авг','Сен','Окт','Ноя','Дек'],
        dayNamesMin: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
        showOn: "focus",
        inline: true
    });

    if (now.getMonth() == 11 && now.getDate() > 20) {
        $('input#id_burial_date').datepicker('option', 'yearRange', '1900:' +  (now_year + 1));
    }
    $('#id_add_dover-issue_date').datepicker('option', 'yearRange', (now_year - 10) + ':' +  (now_year + 1));
    $('#id_add_dover-expire_date').datepicker('option', 'yearRange', (now_year - 10) + ':' +  (now_year + 10));
}

function makeTimePicker(obj) {
    obj.after('<span class="add-on move-left"><i class="icon-time"></i></span>').timepicker({
        showOn: "focus",
        hourText: 'Ч',
        minuteText: 'М',
        showPeriodLabels: false,
        minutes: {
            starts: 0,
            ends: 45,
            interval: 15
        },
        hours: {
            starts: 8,
            ends: 19,
            interval: 1
        },
        inline: true
    });
}

function updateControls() {
    $('span.move-left').remove();
    makeDatePicker($('input[id$=date]'));
    makeDatePicker($('input[id$=date_from]'));
    makeDatePicker($('input[id$=date_to]'));
    makeTimePicker($('input[id*=time]'));
    makeDatePicker($('.modal input[id$=begin]'));
    makeDatePicker($('.modal input[id$=end]'));
    makeDatePicker($('.order_form input[id=id_dt]'));
    setup_address_autocompletes();
}

function updateInnerForm() {
    makeDatePicker($('#block_empty input[id*=date]'));
    makeTimePicker($('#block_empty input[id*=time]'));

    $('#id_customer-customer_type').change();
    setTimeout(function() {
        $('#id_customer-agent_director').change();
    }, 100);
}

function contShowHide(obj, a, c_expand, c_collapse){
    // Свернуть, развернуть:
    // obj,         строка для селектора, объект для свертки
    // a,           строка для селектора, адресная ссылка свертки, развертки
    // c_expand,    строка (или даже html-код) для показа, если надо развернуть
    // c_collapse,  строка (или даже html-код) для показа, если надо свернуть
    if($(a).html() == c_expand){
        $(a).html(c_collapse)
    }else{
        $(a).html(c_expand)
    }
    $(obj).slideToggle();
    return false;
}

$(function() {
    updateControls();
    setup_address_autocompletes();
});

