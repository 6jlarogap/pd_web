app.controller('SupportViewCtrl', function SupportViewCtrl($scope, $routeParams, $location) {
	 "use strict";
	$scope.$on("$routeChangeSuccess", function(event) {
		$scope.title = decodeURI(window.location.search.replace('?title=',''));
		$('.modal, .modal-backdrop').hide();
	});
	
});
