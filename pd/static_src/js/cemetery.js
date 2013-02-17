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

    $('#id_instance_0').live('click', function(){
        var form = $(this).parents('.well');
        form.find('.instance_alert').remove();
        form.prepend('<p class="instance_alert alert">Очистите поля ФИО для нового поиска</p>')
    });

    $('select[name*=fias_]').each(function() {
        if (!$(this).children('option[value!=""]').length) {
            $(this).closest('p').hide();
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
}

function updateAgents() {
    updateAnything($('#id_loru'), $('#id_agent'), LORU_AGENTS);
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
    if (!window.LORU_AGENTS) { LORU_AGENTS = {} }

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
    updateDover();

    $('#id_loru').change(updateAgents);
    updateAgents();

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

    $('input[name=opf]').change(function() {
        if ($('input[name=opf]:checked').val() == 'org') {
            $('#applicant_form_block').hide();
            $('#id_loru').closest('p').show();
            $('#id_agent').closest('p').show();
            $('#id_dover').closest('p').show();

            $('input[name^=person]').closest('p').hide();
            $('#id_org').closest('p').show();
        } else {
            $('#applicant_form_block').show();
            $('#id_loru').closest('p').hide();
            $('#id_agent').closest('p').hide();
            $('#id_dover').closest('p').hide();

            $('input[name^=person]').closest('p').show();
            $('#id_org').closest('p').hide();
        }
    });
    $('input[name=opf]').change();

    $(':input:visible:first').focus();

    $('#id_agent_director').change(function() {
        if ($(this).is(':checked')) {
            $('#id_dover').val('');
            $('#id_dover').closest('p').hide();
            $('#id_agent').val('');
            $('#id_agent').closest('p').hide();
            $('.btn-dover').closest('p').hide();
        } else {
            $('#id_dover').closest('p').show();
            $('#id_agent').closest('p').show();
            $('.btn-dover').closest('p').show();
        }
    });
    $('#id_agent_director').change();

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
    makeDatePicker($('input[id*=date]'));
    makeTimePicker($('input[id*=time]'));
    $('#id_customer-customer_type').change();
    setTimeout(function() {
        $('#id_customer-agent_director').change();
    }, 100);
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

$(function() {
    updateControls();
    setup_address_autocompletes();
});