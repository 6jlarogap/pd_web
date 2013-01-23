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
    $('input').attr('autocomplete', 'off');

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

    $('input.autocomplete[name$=country_name]').attr('autocomplete', 'off').typeahead({
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
    $('input.autocomplete[name$=region_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            var input = $(this)[0].$element;
            typeahead.input_el = input;
            var country = input.parents('.well').find('input[name$=country_name]').val() || '';
            $.ajax({
                url: REGION_URL + "?query=" + query + "&country=" + country,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        },
        onselect: function(val) {
            var $country = $(this)[0].$element.parents('form').find('input[name$=country_name]');
            if (!$country.val()) {
                $country.val(val.country);
            };
            this.$element.val(val.real_value);
        }
    });
    $('input.autocomplete[name$=city_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            var input = $(this)[0].$element;
            var region = input.parents('.well').find('input[name$=region_name]').val() || '';
            var country = input.parents('.well').find('input[name$=country_name]').val() || '';
            $.ajax({
                url: CITY_URL + "?query=" + query + "&country=" + country + "&region=" + region,
                dataType: 'json',
                success: function(data) {
                    typeahead.process(data);
                }
            });
        },
        onselect: function(val) {
            var $region = $(this)[0].$element.parents('form').find('input[name$=region_name]');
            if (!$region.val()) {
                $region.val(val.region);
            }
            var $country = $(this)[0].$element.parents('form').find('input[name$=country_name]');
            if (!$country.val()) {
                $country.val(val.country);
            }
            this.$element.val(val.real_value);
        }
    });
    $('input.autocomplete[name$=street_name]').attr('autocomplete', 'off').typeahead({
        items: 100,
        source: function (typeahead, query) {
            if (query.length < 2) { return }
            var input = $(this)[0].$element;
            var country = input.parents('.well').find('input[name$=country_name]').val() || '';
            var region = input.parents('.well').find('input[name$=region_name]').val() || '';
            var city = input.parents('.well').find('input[name$=city_name]').val() || '';
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
            var $city = $(this)[0].$element.parents('form').find('input[name$=city_name]');
            if (!$city.val()) {
                $city.val(val.city);
            }
            var $region = $(this)[0].$element.parents('form').find('input[name$=region_name]');
            if (!$region.val()) {
                $region.val(val.region);
            }
            var $country = $(this)[0].$element.parents('form').find('input[name$=country_name]');
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

$(function() {
    updateControls();

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

    $('#clean_exhumation').click(function() {
        $('#id_exhumated_date').val('')
    });

    if ($('#exhumation_block input').val()) {
        $('#show_exhumation').hide();
    } else {
        $('#exhumation_block').hide();
        $('#show_exhumation').click(function() {
            $('#exhumation_block').show();
            $('#show_exhumation').hide();
        });
    }

    $('a.load').live('click', function(){
        $('#block_empty').hide();
        $('#block_empty').load(this.href, function() {
            updateControls();
            $('#block_empty').fadeIn('fast', function() {
                $('#id_customer-customer_type').change();
            });
            setup_address_autocompletes();
        });
        return false;
    });

    $('#id_last_name').live('keyup', function() {
        var $check = $(this).closest('.well').find('#id_skip_last_name');
        if ($(this).val()) {
            $check.removeAttr('checked');
        } else {
            $check.attr('checked', '1');
        }
    });

    $('form.in-place').live('submit', function(){
        var url = $(this).attr('action');
        var data = $(this).serialize();
        $.post(url, data, function(data) {
            $('#block_empty').html(data);
            $('.errorlist').addClass('alert');
            updateInnerForm();
            setup_address_autocompletes();
            window.scrollTo(0,0);
        });
        return false;
    });

    $('#id_operation, #id_place, #id_person, #id_client_person, #id_client_organization').live('change', function(){
        var ready = true;
        $('#id_operation, #id_place, #id_person').each(function() {
            if (!$(this).val()) {
                ready = false;
            }
        });

        if (!$('#id_client_person').val() && !$('#id_client_organization').val()) {
            ready = false;
        }

        if (!ready) {
            $('form.main-add .btn-primary').attr('disabled', 'disabled');
        } else {
            $('form.main-add .btn-primary').removeAttr('disabled');
        }
    });

    $('#add_agent_btn').live('click', function() {
        $('#agent_form .form-internal').load($('#agent_form').attr('action'));
    });

    $('#add_dover_btn').live('click', function() {
        $('#dover_form .form-internal').load($('#dover_form').attr('action'), function() {
            updateControls();
            $('#id_customer-agent_person').change();
        });
    });

    $('#id_customer-organization').live('change', function() {
        var options = '<option value="">---------------</option>';
        var org_id = $(this).val();
        var agent;
        var val = $('#id_customer-agent_person').val();
        for(var i in ORG_AGENTS[org_id]) {
            agent = ORG_AGENTS[org_id][i];
            options += '<option value="'+i+'">'+agent.name+'</option>';
        }
        $('#id_customer-agent_person').html(options);
        $('#id_customer-agent_person').val(val);
        if ($('#id_customer-organization').val()) {
            $('#add_agent_btn').show();
            $('#add_dover_btn').show();
        }

        $('#id_customer-agent_person').change();
    });

    $('#id_customer-agent_person').live('change', function() {
        var org_id = $('#id_customer-organization').val();
        var agent_id = $('#id_customer-agent_person').val();
        var agent = ORG_AGENTS && ORG_AGENTS[org_id] && ORG_AGENTS[org_id][agent_id];

        $('#id_customer-agent_doverennost option').remove();
        var options = '<option value="">---------------</option>';
        if (agent) {
            $('#id_add_dover-agent').val(agent.agent_pk);
            var dov_list = agent['dover'];
            for(var i in dov_list) {
                options += '<option value="'+dov_list[i].pk+'">'+dov_list[i].label+'</option>';
            }
        }
        $('#id_customer-agent_doverennost').html(options);
        if (agent) {
            if ($('#id_agent').val() == agent.agent_pk) {
                $('#id_customer-agent_doverennost').val($('#id_doverennost').val() || agent.cur_dov);
            } else {
                $('#id_customer-agent_doverennost').val(agent.cur_dov);
            }
        }
    });

    $('#add_commit').live('click', function() {
        $('#id_add_dover-agent').val($('#id_customer-agent_person').val());
        var url = $('#agent_form').attr('action');
        var send_data = $('#agent_form').serialize();
        $.ajax({
            type: 'POST',
            url: url,
            data: send_data,
            success: function(data) {
                if (data.pk) {
                    var opt = '<option value="'+data.pk+'">'+data.label+'</option>';
                    var org_id = $('#id_customer-organization').val();
                    $('#id_customer-agent_person').append($(opt));
                    $('#id_customer-agent_person').val(data.pk);
                    ORG_AGENTS[org_id][data.pk] = {
                        name: data.label,
                        agent_pk: data.agent_pk,
                        cur_dov: data.cur_dov,
                        dover: data.dover_dict
                    }
                    $('#addAgent').modal('hide');
                } else {
                    $('#agent_form .form-internal').html(data);
                    updateControls();
                }
            },
            error: function(err, errType) {
                console.log(err);
                alert('Ошибка');
            }
        });
    });

    $('#add_dover').live('click', function() {
        var url = $('#dover_form').attr('action');
        var send_data = $('#dover_form').serialize();
        $.ajax({
            type: 'POST',
            url: url,
            data: send_data,
            success: function(data) {
                if (data.pk) {
                    var opt = '<option value="'+data.pk+'">'+data.label+'</option>';
                    var org_id = $('#id_customer-organization').val();
                    var agent_pk = $('#id_customer-agent_person').val();
                    $('#id_customer-agent_doverennost').append($(opt));
                    $('#id_customer-agent_doverennost').val(data.pk);
                    ORG_AGENTS[org_id][agent_pk]['dover'].push({pk: data.pk, label: data.label});
                    $('#addDover').modal('hide');
                } else {
                    $('#dover_form .form-internal').html(data);
                    updateControls();
                }
            },
            error: function(err, errType) {
                console.log(err);
                alert('Ошибка');
            }
        });
    });

    $('#id_operation, #id_place, #id_person').change();

    $('.errorlist').addClass('alert');

    $('#id_customer-customer_type').live('change', function() {
        if ($(this).val() == 1) {
            $('.fields-fizik').slideUp('fast', function() {
                $('.fields-yurik').slideDown('fast');
            });
        } else {
            $('.fields-yurik').slideUp('fast', function() {
                $('.fields-fizik').slideDown('fast');
            });
        }
    });

    $('#id_per_page').parents('p').find('label, :input').css('display', 'inline');
    $('#id_records_order_by').parents('p').find('label, :input').css('display', 'inline');

    $('#id_customer-agent_director').live('change', function() {
        if ($(this).is(':checked') ) {
            $('.fields-agent').slideUp('fast');
        } else {
            $('.fields-agent').slideDown('fast');
        }
    });

    $('#copy_responsible_to_client').live('click', function() {
        var responsible_id = $('#id_responsible').val();
        if (!responsible_id) { return }

        var responsible_name = $('.link-responsible').html();

        var a  = $('<a href="/create/customer/?customer_type=0&instance='+responsible_id+'" class="link-customer load">Отв. '+responsible_name+'</a>');
        $('.link-customer').replaceWith(a);

        $('#id_client_organization').val('').change();
        $('#id_doverennost').val('').change();
        $('#id_agent').val('').change();

        $('#id_client_person').val(responsible_id).change();

        $('.link-customer').click();

        return false;
    });

    $('.dropdown-toggle').dropdown();

    $('#id_cemetery').live('change', function() {
        $(this).closest('.well').find('input').val('');
        $('#place_rooms').text('1');
    })
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