/**
 * Created by PyCharm.
 * User: ilvar
 * Date: 8/17/11
 * Time: 1:02 PM
 * To change this template use File | Settings | File Templates.
 */

function setup_address_autocompletes() {
    //автодополнение страны.
    function completeCountry(event, ui) {
        $(this).val(ui.item.value.split("/")[0]);
        $(this).siblings(':checkbox, label').removeAttr('checked').hide();
        return false;
    }

    $("input:text[id$=country]").autocomplete({
        source: function(term, callback) {
            var id = $(this.element).attr('id').replace(/region/g, '');
            var url = "/getcountries/?term="+term.term;
            var siblings = $(this.element).siblings(':checkbox, label');
            $.getJSON(url, function(data) {
                siblings.removeAttr('checked').show();
                callback(data);
            });
        },
        minLength: 1,
        delay: 100,
        select: completeCountry,
        focus: completeCountry
    });

    //автодополнение региона.
    function completeRegion(event, ui) {
        var id = $(this).attr('id').replace(/region/g, '');
        $(this).val(ui.item.value.split("/")[0]);
        $('#'+id+'country').val(ui.item.value.split("/")[1]);
        $('#'+id+'country').siblings(':checkbox, label').removeAttr('checked').hide();
        $(this).siblings(':checkbox, label').removeAttr('checked').hide();
        return false;
    }

    $("input:text[id$=region]").autocomplete({
        source: function(term, callback) {
            var id = $(this.element).attr('id').replace(/region/g, '');
            var url = "/getregions/?term="+term.term;
            if ($('#'+id+'country').val()) {
                url += "&country=" + $('#'+id+'country').val();
            }
            var siblings = $(this.element).siblings(':checkbox, label');
            $.getJSON(url, function(data) {
                siblings.removeAttr('checked').show();
                callback(data);
            });
        },
        minLength: 2,
        delay: 100,
        select: completeRegion,
        focus: completeRegion
    });

    //автодополнение нас. пункта.
    function completeCity(event, ui) {
        var id = $(this).attr('id').replace(/city/g, '');
        $(this).val(ui.item.value.split("/")[0]);
        $('#'+id+'region').val(ui.item.value.split("/")[1]);
        $('#'+id+'region').siblings(':checkbox, label').removeAttr('checked').hide();
        $('#'+id+'country').val(ui.item.value.split("/")[2]);
        $('#'+id+'country').siblings(':checkbox, label').removeAttr('checked').hide();
        $(this).siblings(':checkbox, label').removeAttr('checked').hide();
        return false;
    }

    $("input:text[id$=city]").autocomplete({
        source: function(term, callback) {
            var id = $(this.element).attr('id').replace(/city/g, '');
            var url = "/getcities/?term="+term.term;
            if ($('#'+id+'country').val()) {
                url += "&country=" + $('#'+id+'country').val();
            }
            if ($('#'+id+'region').val()) {
                url += "&region=" + $('#'+id+'region').val();
            }
            var siblings = $(this.element).siblings(':checkbox, label');
            $.getJSON(url, function(data) {
                siblings.removeAttr('checked').show();
                callback(data);
            });
        },
        minLength: 2,
        delay: 100,
        select: completeCity,
        focus: completeCity

    });
    //автодополнение улицы.
    function completeStreet(event, ui) {
        var id = $(this).attr('id').replace(/street/g, '');
        $(this).val(ui.item.value.split("/")[0]);
        $('#'+id+'city').val(ui.item.value.split("/")[1]);
        $('#'+id+'city').siblings(':checkbox, label').removeAttr('checked').hide();
        $('#'+id+'region').val(ui.item.value.split("/")[2]);
        $('#'+id+'region').siblings(':checkbox, label').removeAttr('checked').hide();
        $('#'+id+'country').val(ui.item.value.split("/")[3]);
        $('#'+id+'country').siblings(':checkbox, label').removeAttr('checked').hide();
        $(this).siblings(':checkbox, label').removeAttr('checked').hide();
        return false;
    }

    $("input:text[id$=street]").autocomplete({
        source: function(term, callback) {
            var id = $(this.element).attr('id').replace(/street/g, '');
            var url = "/getstreets/?term="+term.term;
            if ($('#'+id+'country').val()) {
                url += "&country=" + $('#'+id+'country').val();
            }
            if ($('#'+id+'region').val()) {
                url += "&region=" + $('#'+id+'region').val();
            }
            if ($('#'+id+'city').val()) {
                url += "&city=" + $('#'+id+'city').val();
            }
            var siblings = $(this.element).siblings(':checkbox, label');
            $.getJSON(url, function(data) {
                siblings.removeAttr('checked').show();
                callback(data);
            });
        },
        minLength: 2,
        delay: 100,
        select: completeStreet,
        focus: completeStreet

    });
}

$(function() {
    setup_address_autocompletes();
});
