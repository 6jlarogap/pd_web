app.factory('Place', function ($resource, $routeParams) {
  return $resource('/api/place/:placeID/:action', {placeID: '@id'}, {
    get: {
      method: 'GET',
      params: {
        format: 'json'
      },
      isArray: false
    },
    getForm: {
      method: 'GET',
      params: {
        action: 'getform',
      },
      isArray: false
    },
    cancelExhumation: {
      method: 'GET',
      params: {
        action: 'cancel_exhumation',
      },
      isArray: false
    },
    getGraves: {
      method: 'GET',
      params: {
        action: 'getgraves',
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
    deletePhoto: {
      method: 'DELETE',
      params: {
        action: 'deletephoto'
      }
    },
    save: {
      method: 'POST',
      params: {
        format: 'json'
      }
    },
    list_cemetery: {
      method: 'GET',
      params: {
        format: 'json'
      },
      isArray: true
    },

  });
});
