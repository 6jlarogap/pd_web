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
    
        "js/app/directive/angular-ymaps.js",
        
        "js/app/directive/file_upload.js",
    
        "js/app/controller/cemetery.js",
        "js/app/controller/cemetery_view.js",
        "js/app/controller/area_view.js",
        "js/app/controller/place_view.js",
        filters='jsmin', output='pd.js')


js_angular = Bundle(
        "js/angular3d/ui-bootstrap-0.5.0.js",
        "js/angular3d/ui-bootstrap-tpls-0.5.0.js",
        "js/bootstrap-typeahead.js",
        "js/angular3d/ng-grid/ng-grid-2.0.7.debug.js",
        "js/angular3d/ng-grid/i18n/ru.js",
        "js/libs/lodash.compat.min.js",
        filters='jsmin', output='pd-angular.js')


css_app = Bundle(
        "js/angular3d/ng-grid/ng-grid.min.css",
        "js/app/app.css",
        filters='cssmin', output='pd.css')


register('js_app', js_app)
register('js_angular', js_angular)
register('css_app', css_app)
