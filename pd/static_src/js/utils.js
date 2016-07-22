var escapeRegExp;

(function () {
    // Referring to the table here:
    // https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/regexp
    // these characters should be escaped
    // \ ^ $ * + ? . ( ) | { } [ ]
    // These characters only have special meaning inside of brackets
    // they do not need to be escaped, but they MAY be escaped
    // without any adverse effects (to the best of my knowledge and casual testing)
    // : ! , =
    // my test "~!@#$%^&*(){}[]`/=?+\|-_;:'\",<.>".match(/[\#]/g)

    var specials = [
            // order matters for these
            "-"
            , "["
            , "]"
            // order doesn't matter for any of these
            , "/"
            , "{"
            , "}"
            , "("
            , ")"
            , "*"
            , "+"
            , "?"
            , "."
            , "\\"
            , "^"
            , "$"
            , "|"
        ]

    // I choose to escape every character with '\'
    // even though only some strictly require it when inside of []
        , regex = RegExp('[' + specials.join('\\') + ']', 'g')
        ;

    escapeRegExp = function (str) {
        return str.replace(regex, "\\$&");
    };

    // test escapeRegExp("/path/to/res?search=this.that")
}());

function updateProductId() {
    var initial_forms = $('#id_orderitem_set-INITIAL_FORMS').val();
    $('.dynamic-form input[type=hidden]').each(function(index) {
        var val = (index +1 <= initial_forms) ? index + 1 : '';
        $(this).val('');
    });
}


function updateElementIndex(el, prefix, ndx, is_new_form) {
    is_new_form = typeof is_new_form !== 'undefined' ? is_new_form : false;
    row = $(el).attr('id', prefix + '-' + ndx + '-row');
    row.children('td:first').html(ndx + 1);
    product_field_name = prefix + '-' + ndx + '-product';
    row.children('td:first').next().next().children().attr('name', product_field_name).attr('id', 'id_' + product_field_name);
    cost_field_name = prefix + '-' + ndx + '-cost';
    row.children('td:first').next().next().next().children().attr('name', cost_field_name).attr('id', 'id_' + cost_field_name);
    quantity_field_name = prefix + '-' + ndx + '-quantity';
    row.children('td:first').next().next().next().next().children().attr('name', quantity_field_name).attr('id', 'id_' + quantity_field_name);
    id_field_name = prefix + '-' + ndx + '-id';
    row.find('input[type=hidden]').attr('name', id_field_name).attr('id', 'id_' + id_field_name).attr('id', 'id_' + id_field_name);
    if (is_new_form) {
        $('#id_'+ product_field_name).val('');
        $('#id_' + cost_field_name).attr('value', '');
        $('#id_' + quantity_field_name).attr('value', '');
        $(el).find('td.amount input[type=text]').attr('value', '');
    }
}

function addForm(btn, prefix) {
    var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    var row = $('.dynamic-form:last').clone(true).get(0);
    $(row).find('.selectArea').remove();
    $(row).find('.outtaHere').removeClass('outtaHere');
    $(row).attr('id', prefix + '-' + formCount + '-row').insertAfter($('.dynamic-form:last')).children('.hidden').removeClass('hidden');
    $(row).each(function() {
        updateElementIndex(this, prefix, formCount, true);
        $(this).val('');
    });
    $(row).find('.delete-row').click(function() {
        deleteForm(this, prefix);
    });
    $('#id_' + prefix + '-TOTAL_FORMS').val(formCount + 1);
    $('#' + prefix + '-' + formCount + '-row td:first').html(formCount + 1);
    updateProductId();
    hideShowDelete()
    return false;
}

function deleteForm(btn, prefix) {
    $(btn).parents('.dynamic-form').remove();
    var forms = $('.dynamic-form');
    $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
    for (var i=0, formCount=forms.length; i<formCount; i++) {
        $(forms.get(i)).each(function() {
            updateElementIndex(this, prefix, i);
        });
    }
    updateProductId();
    updateTotalForm();
    hideShowDelete()
    return false;
}

function hideShowDelete() {
    if ($('.dynamic-form').length > 1) {
        $('.delete-row').show();
    } else {
        $('.delete-row').hide();
    }
}
    
function removeEmptyForms() {
    while (true) {
        var to_delete = [];
        var forms = $('.dynamic-form');
        for (var i=0, formCount=forms.length; i<formCount; i++) {
            $(forms.get(i)).each(function() {
                $(this).find('.product_type').find('select').each(function() {
                    if (!$(this).val()) {
                        to_delete.push($(this));
                    }
                });
            });
            if (to_delete.length > 0) {
                deleteForm(to_delete[0], 'orderitem_set');
                break;
            }
        }
        if (i >= formCount) {
            break;
        }
    }
    return true;
}

function updateAmountForm(el) {
    var cost = el.find('.product_cost input').val();
    var quantity = el.find('.product_quantity input').val();
    if (cost && quantity) {
        var amount = cost * quantity;
        el.find('.amount input').val(amount.toFixed(2));
    }
}

function updateTotalForm() {
    var total = 0;
    $('.amount input').each(function() {
        if ($(this).val())
            total += parseFloat($(this).val());
    });
    if ($('#id_do_photo').length) {
        var price_photo = parseFloat($('#id_price_photo').val());
        if ($('#id_do_photo').is(':checked')) {
            total += price_photo;
        }
    }
    $('#id_total').val(total.toFixed(2));
}

function strTruncate_(str, n, useWordBoundary) {
    var singular,
        tooLong = str.length > n;
    useWordBoundary = useWordBoundary || true;

    // Edge case where someone enters a ridiculously long string.
    str = tooLong ? str.substr(0, n-1) : str;

    singular = (str.search(/\s/) === -1) ? true : false;
    if(!singular) {
      str = useWordBoundary && tooLong ? str.substr(0, str.lastIndexOf(' ')) : str;
    }

    return  tooLong ? str + '&hellip;' : str;
}
