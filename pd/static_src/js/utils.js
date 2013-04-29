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


function updateElementIndex(el, prefix, ndx) {
    var id_regex = new RegExp('(' + prefix + '-\\d+)');
    var replacement = prefix + '-' + ndx;
    if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
    if (el.id) el.id = el.id.replace(id_regex, replacement);
    if (el.name) el.name = el.name.replace(id_regex, replacement);
}

function addForm(btn, prefix) {
    var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    var row = $('.dynamic-form:last').clone(true).get(0);
    $(row).find('.selectArea').remove();
    $(row).find('.outtaHere').removeClass('outtaHere');
    $(row).attr('id', prefix + '-' + formCount + '-row').insertAfter($('.dynamic-form:last')).children('.hidden').removeClass('hidden');
    prev_count_form = formCount - 1;
    $('#' + prefix + '-' + prev_count_form + '-row td:last span').addClass('hidden');
    $(row).children().not(':last').children().each(function() {
        updateElementIndex(this, prefix, formCount);
        $(this).val('');
    });
    $(row).find('.delete-row').click(function() {
        deleteForm(this, prefix);
    });
    $('#id_' + prefix + '-TOTAL_FORMS').val(formCount + 1);
    $('#' + prefix + '-' + formCount + '-row td:first').html(formCount + 1);
    $('#' + prefix + '-' + formCount + '-row td:last span').removeClass('hidden');
    return false;
}

function deleteForm(btn, prefix) {
    $(btn).parents('.dynamic-form').remove();
    var forms = $('.dynamic-form');
    $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
    for (var i=0, formCount=forms.length; i<formCount; i++) {
        $(forms.get(i)).children().not(':last').children().each(function() {
            updateElementIndex(this, prefix, i);
        });
    }
    prev_count_form = forms.length - 1;
    if (prev_count_form != 0)
        $('#' + prefix + '-' + prev_count_form + '-row td:last span').removeClass('hidden');
    return false;
}