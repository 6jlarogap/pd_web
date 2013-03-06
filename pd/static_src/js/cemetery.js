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
    ORG_URL = '/autocomplete/org/';


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

    $('#mainform #id_applicant_org').attr('autocomplete', 'off').typeahead({
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

    $('#mainform #id_applicant_person').attr('autocomplete', 'off').typeahead({
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
    updateAnything($('#id_applicant_organization'), $('#id_agent'), LORU_AGENTS);
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
    if (!window.PLACE_TYPES) { PLACE_TYPES = {} }

    $('.burial-form,.order_form').find(':input').live('keypress', function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
            $(this).change();
            return false;
        }
    });

    $('.burial-form,.order_form').find(':input').live('blur', function(e) {
        $(this).change();
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

    $('input[name=opf]').change(function() {
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
            $('input[name=payment][value=wire]').attr('checked', '1');

            $('#id_applicant-last_name').val('');
        } else {
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
            $('input[name=payment][value=cash]').attr('checked', '1');

            $('#id_applicant_organization').val('');
            $('#id_agent_director').val('');
            $('#id_agent').val('');
            $('#id_dover').val('');
        }
    });
    $('input[name=opf]').change();

    $('form.burial-form :input:visible:first').focus();

    $('#id_agent_director').change(function() {
        if ($(this).is(':checked')) {
            $('#id_dover').closest('p').hide();
            $('#id_agent').closest('p').hide();
            $('.btn-dover').closest('p').hide();
            $('.btn-agent').closest('p').hide();
        } else {
            $('#id_dover').closest('p').show();
            $('#id_agent').closest('p').show();
            $('#id_applicant_organization').change();
        }
    });
    $('#id_agent_director:visible').change();

    $('#add_agent').find('.btn-primary').click(function() {
        var loru_pk = $('#id_applicant_organization').val();
        if (!loru_pk) {
            return alert('Выберите ЛОРУ');
        }
        var data = $('#add_agent form').serialize();
        $.post('/burials/add_agent/?loru='+loru_pk, data, function(data){
            if (data.pk) {
                $('#id_agent').append('<option value="'+data.pk+'">'+data.label+'</option>');
                $('#id_dover').append('<option value="'+data.dover_pk+'">'+data.dover_label+'</option>');
                $('#id_agent').val(data.pk);
                $('#id_dover').val(data.dover_pk);
                if (!LORU_AGENTS[loru_pk]) {
                    LORU_AGENTS[loru_pk] = [];
                }
                LORU_AGENTS[loru_pk].push([data.pk, data.label])
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
        $.post('/burials/add_org/', data, function(data){
            if (data.pk) {
                var select = $('#id_applicant_organization');
                select.append('<option value="'+data.pk+'">'+data.label+'</option>');
                select.val(data.pk);
                $('#add_loru').modal('hide');
                $('#add_loru form :input').val('');
                select.change();
            } else {
                alert(data);
            }
        })
    });

    $('#add_org').find('.btn-primary').click(function() {
        var data = $('#add_org form').serialize();
        $.post('/burials/add_org/', data, function(data){
            if (data.pk) {
                var select = $('#id_org');
                select.append('<option value="'+data.pk+'">'+data.label+'</option>');
                select.val(data.pk);
                $('#add_org').modal('hide');
                $('#add_org form :input').val('');
                select.change();
            } else {
                alert(data);
            }
        })
    });

    old_grave_value = $('#id_grave_number').val();

    $('#id_cemetery, #id_area, #id_row, #id_place_number').change(function() {
        $('#id_grave_number').html('<option value="1">1</option>');
        $('#id_responsible-take_from_0').removeAttr('checked').closest('li').hide();
        if ($('#id_cemetery').val() &&  $('#id_area').val() &&  $('#id_place_number').val()) {
            var data = $('#id_cemetery, #id_area, #id_row, #id_place_number').serialize();
            $('#place_info').load('/burials/get_place/?'+data)
            $('#id_grave_number').val(old_grave_value);
        } else if ($('#id_cemetery').val() &&  $('#id_area').val()) {
            var data = $('#id_cemetery, #id_area, #id_row, #id_place_number').serialize();
            $('#place_info').load('/burials/get_place/?'+data)
            $('#id_grave_number').val(old_grave_value);
        }

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

    var ac_options = {
        bounds: USER_DEFAULT_BOUNDS,
        types: ['geocode'],
        componentRestrictions: {country: 'ru'}
    };
    $('input[id$=fias_address]').attr('autocomplete', 'off').css('width', '600px').each(function() {
        var autocomplete = new google.maps.places.Autocomplete(this, ac_options );
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

        var geocoder = new YMaps.Geocoder(addr, {'prefLang': 'ru'});
        YMaps.Events.observe(geocoder, geocoder.Events.Load, function () {
            if (this.length()) {
                var country = '', region = '', city = '', street = '';
                var house = '', building = '', block = '', flat = '';
                form_block.find('[id$=post_index], [id$=country_name], [id$=region_name], [id$=city_name]').val('');
                form_block.find('[id$=street_name]').val('');

                var obj = this._objects[0].AddressDetails;
                if (obj.Country) {
                    country = obj.Country.CountryName;
                    form_block.find('input[id$=country_name]').val(country);
                    if (obj.Country.AdministrativeArea) {
                        region = obj.Country.AdministrativeArea.AdministrativeAreaName;
                        if (obj.Country.AdministrativeArea.Locality) {
                            city = obj.Country.AdministrativeArea.Locality.LocalityName;
                            if (obj.Country.AdministrativeArea.Locality.Thoroughfare) {
                                street = obj.Country.AdministrativeArea.Locality.Thoroughfare.ThoroughfareName;
                            }
                        }
                    }


                    if (country) {
                        var data = 'country=' + country + '&region=' + region + '&city=' + city + '&street=' + street +
                            '&house=' + house + '&block=' + block + '&building=' + building + '&flat=' + flat;
                        var fias_url = '/geo/autocomplete/fias/?'+data;
                        $.getJSON(fias_url, function(data) {
                            if (data.ok) {
                                street_input.val(data.id);
                                form_block.find('.fias_street_info').html(data.info);
                                form_block.find('.fias_street_info').show();
                                form_block.find('.full_address').hide();
                            } else {
                                street_input.val('');
                                form_block.find('.fias_street_info').html('');
                                form_block.find('.fias_street_info').hide();
                                form_block.find('.full_address').show();

                                form_block.find('input[id$=region_name]').val(region);
                                form_block.find('input[id$=city_name]').val(city);
                                form_block.find('input[id$=street_name]').val(street);
                            }
                        })
                    }
                }
            } else {
                alert("Адрес неразборчив, вводите в виде: улица Свободы, Новороссийск, Краснодарский край");
            }
        })
        YMaps.Events.observe(geocoder, geocoder.Events.Fault, function (geocoder, errorMessage) {
            alert("Произошла ошибка: " + errorMessage)
        });

//        var geocoder = new google.maps.Geocoder();
//        geocoder.geocode( { 'address': addr, 'language': 'ru' }, function(results, status) {
//            if (status == google.maps.GeocoderStatus.OK) {
//                var country = '', region = '', city = '', street = '';
//                var house = '', building = '', block = '', flat = '';
//                form_block.find('[id$=post_index], [id$=country_name], [id$=region_name], [id$=city_name]').val('');
//                form_block.find('[id$=street_name]').val('');
//
//                var address = results[0].address_components;
//                $(address).each(function() {
//                    if (this.types.indexOf("postal_code") > -1) { form_block.find('input[id$=post_index]').val(this.long_name); }
//                    if (this.types.indexOf("country") > -1) { country = this.long_name; form_block.find('input[id$=country_name]').val(country); }
//                    if (this.types.indexOf("administrative_area_level_1") > -1) { region = this.long_name; form_block.find('input[id$=region_name]').val(''); }
//                    if (this.types.indexOf("locality") > -1) { city = this.long_name; form_block.find('input[id$=city_name]').val(''); }
//                    if (this.types.indexOf("route") > -1) { street = this.long_name; form_block.find('input[id$=street_name]').val(''); }
//                    if (this.types.indexOf("street_number") > -1) {
//                        form_block.find('input[id$=house]').val(this.long_name);
//                        house = this.long_name;
//                        if (this.long_name.indexOf("корпус") > -1) {
//                            var bits = this.long_name.split(" корпус ");
//                            form_block.find('input[id$=house]').val(bits[0]);
//                            form_block.find('input[id$=block]').val(bits[1]);
//                            house = bits[0];
//                            block = bits[1];
//                        }
//                        if (this.long_name.indexOf("строение") > -1) {
//                            var bits = this.long_name.split(" строение ");
//                            form_block.find('input[id$=house]').val(bits[0]);
//                            form_block.find('input[id$=building]').val(bits[1]);
//                            house = bits[0];
//                            building = bits[1];
//                        }
//                    }
//                    if (this.types.indexOf("subpremise") > -1) {
//                        flat = this.long_name;
//                        form_block.find('input[id$=flat]').val(this.long_name);
//                    }
//                });
//
//                if (country) {
//                    var data = 'country=' + country + '&region=' + region + '&city=' + city + '&street=' + street +
//                        '&house=' + house + '&block=' + block + '&building=' + building + '&flat=' + flat;
//                    var fias_url = '/geo/autocomplete/fias/?'+data;
//                    $.getJSON(fias_url, function(data) {
//                        if (data.ok) {
//                            street_input.val(data.id);
//                            form_block.find('.fias_street_info').html(data.info);
//                            form_block.find('.fias_street_info').show();
//                            form_block.find('.full_address').hide();
//                        } else {
//                            street_input.val('');
//                            form_block.find('.fias_street_info').html('');
//                            form_block.find('.fias_street_info').hide();
//                            form_block.find('.full_address').show();
//
//                            form_block.find('input[id$=region_name]').val(region);
//                            form_block.find('input[id$=city_name]').val(city);
//                            form_block.find('input[id$=street_name]').val(street);
//                        }
//                    })
//                }
//            } else {
//                alert("Адрес неразборчив, вводите в виде: улица Свободы, Новороссийск, Краснодарский край")
//            }
//        })
    });
    $('input[id$=fias_address]').change();

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
    makeDatePicker($('.modal input[id$=begin]'));
    makeDatePicker($('.modal input[id$=end]'));
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