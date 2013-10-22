/*
	Google locations bind
    <google-search location=location></google-search>

 * */
angular.module('googleObjects', []).
    directive('googleSearch', function($rootScope){
        return {
            restrict:'E',
            replace:true,
            // transclude:true,
            scope: {location:'='},
            template: '<input id="google_places_r" name="google_places_ac" type="text" autocomplete="off" class="span12 input-block-level"/>',
            link: function($scope, elm, attrs){
                var autocomplete = new google.maps.places.Autocomplete($("#google_places_r")[0], {});
                google.maps.event.addListener(autocomplete, 'place_changed', function() {
                    var place = autocomplete.getPlace();
                    $scope.$parent.search_callback(parse_address(place));
                    $scope.$apply();
                });
            }
        }
    });
    



function parse_address(result) {
	/*
	 * Извлекает из запроса google адрес
	 */
	if (!result) {
		return
	}
	var address = result.address_components, item = {};
	$(address).each(function() {
		if (this.types.indexOf("postal_code") > -1) {
			item.postal_code = this.long_name;
		}
		if (this.types.indexOf("country") > -1) {
			item.country = this.long_name;
		}
		if (this.types.indexOf("administrative_area_level_1") > -1) {
			item.region = this.long_name;
		}
		if (this.types.indexOf("locality") > -1) {
			item.city = this.long_name;
		}
		if (this.types.indexOf("route") > -1) {
			item.street = this.long_name;
		}
		if (this.types.indexOf("street_number") > -1) {
			item.house = this.long_name;
			if (this.long_name.indexOf("корпус") > -1) {
				var bits = this.long_name.split(" корпус ");
				item.house = bits[0];
				item.block = bits[1];
			}
			if (this.long_name.indexOf("строение") > -1) {
				var bits = this.long_name.split(" строение ");
				item.house = bits[0];
				item.building = bits[1];
			}
		}
		if (this.types.indexOf("subpremise") > -1) {
			item.flat = this.long_name;
		}
	});
	return item;
}
