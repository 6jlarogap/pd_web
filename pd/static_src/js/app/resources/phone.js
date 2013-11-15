app.factory('Phone', function($resource,$routeParams){
	return $resource('/api/alive-person-phone/:phoneID', {phoneID: '@id'})
});
