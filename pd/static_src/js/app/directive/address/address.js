app.directive("address", ["$rootScope", function ($rootScope) {
  return {
    restrict: "EA",
    templateUrl: STATIC_APP_URL + '/directive/address/address.html' + version_str,
    scope: {
      data: '=',
      save_action: '&'
    },

    controller: ['$scope', '$dialog', '$http', '$resource', 'Place',
      function ($scope, $dialog, $http, $resource, $parse, Place) {

        $scope.location = '';
        $scope.location_place = undefined;

        $scope.showMore = false;
        $scope.opts = {
          backdropFade: true,
          dialogFade: true
        };

        function resultFormater(state) {
          return state.name;
        }

        $scope.search_callback = function (data) {
          if (!data)
            return;
          $scope.editor.country.name = data.country;
          $scope.editor.region.name = data.region;
          $scope.editor.city.name = data.city;
          $scope.editor.street.name = data.street;
          $scope.editor.post_index = data.postal_code;
          // $scope.data.house = data.house;
          $scope.editor.flat = data.flat;
          $("input.country").val($scope.editor.country.name);
          $("input.region").val($scope.editor.region.name);
          $("input.city").val($scope.editor.city.name);
          $("input.street").val($scope.editor.street.name);
          $("input.house").val($scope.editor.house);
          $("input.flat").val($scope.editor.flat);
          var fields = [ 'block', 'flat', 'house', 'street', 'city', 'region', 'country', 'postal_code' ];
          for (var i = 1; i < fields.length; i++) {
            if (data[fields[i]] != undefined) {
              $('#id_address-' + fields[i]).focus();
              break;
            }
          }
        };

        // Diallog
        $scope.isAddressEditorOpen = false;

        $scope.open = function () {
          $scope.isAddressEditorOpen = true;
          $scope.$parent.$parent.editor.isAddressEdited = true;
          $scope.editor = angular.copy($scope.data);
        };

        $scope.close = function () {
          $scope.isAddressEditorOpen = false;
          $scope.$parent.$parent.editor.isAddressEdited = false;
          $scope.editor = angular.copy($scope.data);
        };

        $scope.save = function (form) {
          $scope.data = $scope.editor;
          $scope.isAddressEditorOpen = false;
          $scope.$parent.$parent.editor.isAddressEdited = false;
        };

        $scope.form_disabled = function () {
          var item = $scope.editor;
          if (!item)
            return;
          var c = item.country.name && item.country.name.length > 0,
            r = item.region.name && item.region.name.length > 0,
            ci = item.city.name && item.city.name.length > 0,
            s = item.street.name && item.street.name.length > 0;
          var res =
            c && !r && !ci && !s
              || c && r && !ci && !s
              || c && r && ci && !s
              || c && r && ci && s;
          $scope.$parent.$parent.editor.isAddressValid = res;
          return !res;
        }

        // EOF Diallog
      }],

    link: function ($scope, elem, attr, addressCtrl) {
      // Address autopopulate
      function completeCountry(event, ui) {
        var data = ui.item.value.split("/");
        $scope.data.country.name = data[0];
        $(this).val($scope.data.country.name);
        return false;
      };
      function completeRegion(event, ui) {
        var data = ui.item.value.split("/");
        $scope.data.country.name = data[1];
        $scope.data.region.name = data[0];
        $(this).val($scope.data.region.name);
        return false;
      };
      function completeCity(event, ui) {
        var data = ui.item.value.split("/");
        $scope.data.country.name = data[2];
        $scope.data.region.name = data[1];
        $scope.data.city.name = data[0];
        $(this).val($scope.data.city.name);
        return false;
      };
      function completeStreet(event, ui) {
        var data = ui.item.value.split("/");
        $scope.data.country.name = data[3];
        $scope.data.region.name = data[2];
        $scope.data.city.name = data[1];
        $scope.data.street.name = data[0];
        $(this).val($scope.data.street.name);
        return false;
      };
      elem.find("input.country").autocomplete({
        source: function (term, callback) {
          var url = "/geo/autocomplete/country/?query=" + term.term;
          $.getJSON(url, function (data) {
            callback(data);
          });
        },
        minLength: 2,
        delay: 100,
        select: completeCountry,
        focus: completeCountry
      });

      elem.find("input.region").autocomplete({
        source: function (term, callback) {
          var url = "/geo/autocomplete/region/?query=" + term.term;
          url += "&country=" + $scope.data.country.name;
          $.getJSON(url, function (data) {
            callback(data);
          });
        },
        minLength: 2,
        delay: 100,
        select: completeRegion,
        focus: completeRegion
      });

      elem.find("input.city").autocomplete({
        source: function (term, callback) {
          var url = "/geo/autocomplete/city/?query=" + term.term;
          with ($scope.data)
            url += "&region=" + region.name + "&country=" + country.name;
          $.getJSON(url, function (data) {
            callback(data);
          });
        },
        minLength: 2,
        delay: 100,
        select: completeCity,
        focus: completeCity
      });

      elem.find("input.street").autocomplete({
        source: function (term, callback) {
          var url = "/geo/autocomplete/street/?query=" + term.term;
          with ($scope.data)
            url += "&country=" + country.name + "&region=" + region.name + "&city=" + city.name;
          $.getJSON(url, function (data) {
            callback(data);
          });
        },
        minLength: 2,
        delay: 100,
        select: completeStreet,
        focus: completeStreet
      });
    }
  }
}]);
