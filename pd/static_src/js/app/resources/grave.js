app.factory('Grave', function($resource, $routeParams){
	return $resource('/api/grave/:graveID/:action', {graveID:'@id'},{
		get: {
			method: 'GET',
			params: {
				format: 'json'
			},
			isArray: false
		},
		query: {
			method: 'GET',
			params: {
				format: 'json'
			},
			isArray: true
		},
		update: {
			method: 'PUT',
            params: {
            }
		},
        save: {
            method: 'POST',
            params: {
            }
        },
        move: {
            method: 'GET',
            params: {
            	action: 'move',
            }
        }
	});
});
