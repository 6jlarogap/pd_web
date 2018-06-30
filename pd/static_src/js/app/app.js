// 'use strict';
var APP_VERSION = '0.1.0-61',
	version_str = '?v='+APP_VERSION,
	test, qqq;

var app = angular.module('angularPD', ['ngGrid', 'ngCookies', 'ngResource', 'ui.bootstrap', 
	'ui.bootstrap.dialog', 'googleObjects', 'blueimp.fileupload', 'ui.mask', 'ui.validate', 'ymaps', 'naturalSort'], //'pd.address',  
function($routeProvider, $locationProvider, $dialogProvider) {
	$locationProvider.html5Mode(true);
    $dialogProvider.options({
    	backdropClick: false, 
    	dialogFade: false
	});
})
.config(function($routeProvider){

    $routeProvider.
	    when('/manage/cemetery/', {
	        controller: 'CemeteryCtrl',
	        templateUrl: STATIC_TPL_URL+'/manage/cemetery_list.html'+version_str
	    }).when('/manage/cemetery/:cemetery_id', {
	        controller: 'CemeteryViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/manage/cemetery_view.html'+version_str
	    }).when('/manage/cemetery/:cemetery_id/area/:area_id', {
	        controller: 'AreaViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/manage/area_view.html'+version_str
	    }).when('/manage/cemetery/:cemetery_id/area/:area_id/place/:place_id', {
	        controller: 'PlaceViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/manage/place_view.html'+version_str

	    }).when('/manage/500', {
	        controller: 'SupportViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/page500.html'+version_str
	    }).when('/manage/500?title=:title', {
	        controller: 'SupportViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/page500.html'+version_str
	    }).when('/manage/404?title=:title', {
	        controller: 'SupportViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/page404.html'+version_str
	    }).otherwise({
	    	controller: 'SupportViewCtrl',
	        templateUrl: STATIC_TPL_URL+'/page404.html'+version_str
	    });
});

app.directive('pdDtCheckbox', function () {
  return {
    restrict: 'A',
    require: 'ngModel',
    link: function (scope, iElement, iAttrs, ngModelController) {
      ngModelController.$formatters.push(function (value) {
        return !!value;
      });
      ngModelController.$parsers.push(function (value) {
        return true === value ? (new Date()).toISOString() : null;
      });
    }
  };
});
