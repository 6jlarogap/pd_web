from django_assets import Bundle, register

js_app = Bundle(
        "js/app/const.js",
        "js/app/app.lib.js",
        "js/app/app.js",
        "js/app/app.config.js",
        "js/app/app.filter.js",

        "js/app/resources/place.js",
        "js/app/resources/cemetery.js",
        "js/app/resources/grave.js",
        "js/app/resources/burial.js",
        "js/app/resources/area.js",
        "js/app/resources/area_purpose.js",
        "js/app/resources/area_photo.js",
        "js/app/resources/grave_photo.js",
        "js/app/resources/person.js",
        "js/app/resources/log.js",
    
        "js/app/directive/address/address.js",
        "js/app/directive/google.js",
    
        "angular-ui-bootstrap/src/dialog/dialog.js",
    
        "js/app/directive/angular-ymaps.js",
        
        "js/app/directive/file_upload.js",
    
        "js/app/controller/cemetery.js",
        "js/app/controller/cemetery_view.js",
        "js/app/controller/area_view.js",
        "js/app/controller/place_view.js",
        filters='jsmin', output='pd.js')


js_angular = Bundle(
        
        # #############################

        "angular/angular.min.js",
        "angular-resource/angular-resource.min.js",
        "angular-cookies/angular-cookies.min.js",

        "angular-bootstrap/ui-bootstrap.min.js",
        "angular-bootstrap/ui-bootstrap-tpls.min.js",

        "select2/select2.min.js",
        "select2/select2_locale_ru.js",

        "ng-grid/ng-grid-2.0.7.min.js",


        #<!-- script type="text/javascript" src="{{ STATIC_URL }}js/angular/angular-bootstrap.js"></script --><!-- * -->
        #<!-- script type="text/javascript" src="{{ STATIC_URL }}js/angular/i18n/angular-locale_ru-ru.js"></script --><!-- * -->
        
        #<!--"js/angular3d/select2.js",-->
    
        "js/bootstrap-typeahead.js",
        
        #<!--script type="text/javascript" src="{{ STATIC_URL }}js/angular3d/ng-grid/i18n/ru.js"></script-->
        #<!--script type="text/javascript" src="{{ STATIC_URL }}js/angular3d/bootstrap-typeahead.js"></script-->
        "lodash/dist/lodash.compat.min.js",
        # #############################


        "js/bootstrap-typeahead.js",
        "ng-grid/ng-grid-2.0.7.min.js",
        #"ng-grid/ng-grid/src/i18n/ru.js",
        "lodash/dist/lodash.min.js",
        filters='jsmin', output='pd-angular.js')


css_app = Bundle(
        "select2/select2.css",
        "ng-grid/ng-grid.min.css",
        "js/app/app.css",
        filters='cssmin', output='pd.css')


register('js_app', js_app)
register('js_angular', js_angular)
register('css_app', css_app)
