﻿app.controller('AddressController', ['$scope', '$dialog', '$http', '$resource', 'Place',
function($scope, $dialog, $http, $resource, $parse, Place) {
	var self = this;

	$scope.location = '';
	$scope.location_place = undefined;

	$scope.showMore = false;
	$scope.opts = {
		backdropFade : true,
		dialogFade : true
	};
	var Cemetery = $resource('/api/cemetery/:cemeteryID?address_id=:addressID', {
		cemeteryID : '@id',
		addressID : '@address'
	}, {
		update : {
			method : 'PUT'
		}
	});
	var Address = $resource('/api/geo/location/:addressID', {
		addressID : '@id'
	}, {
		update : {
			method : 'PUT'
		}
	});

	var AddressStatic = $resource('/api/geo/location/static/:addressID', {
		addressID : '@id'
	}, {
		update : {
			method : 'PUT'
		}
	});

	function resultFormater(state) {
		return state.name;
	}

	function get_id(el) {
		var id = 0;
		if ($scope.address && $scope.address[el])
			id = $scope.address[el].id;
		return id;
	}
	$scope.search_callback = function(data) {
		if (!data)
			return;
		$scope.item.country = data.country;
		$scope.item.region = data.region;
		$scope.item.city = data.city;
		$scope.item.street = data.street;
		$scope.item.post_index = data.postal_code;
		$scope.item.house = data.house;
		$scope.item.flat = data.flat;
		$("input.country").val($scope.item.country);
		$("input.region").val($scope.item.region);
		$("input.city").val($scope.item.city);
		$("input.street").val($scope.item.street);
		$("input.house").val($scope.item.house);
		$("input.flat").val($scope.item.flat);
		$scope.digest
		var fields = ['block', 'flat', 'house', 'street', 'city', 'region', 'country', 'postal_code'];
		for(var i=1;i<fields.length;i++){
			if(data[fields[i]]!=undefined){
				$('#id_address-'+fields[i]).focus();
				q = $('#id_address-'+fields[i]);
				break;
			}
		}
	};
	
	$scope.update = function() {
		if ($scope.address) {
			Address.get({
				addressID : $scope.address
			}, function(result) {
				$scope.item = result;
			});
		} else {
			$scope.item = new Address();
			$scope.item.is_new = true;
		}
	};

	$scope.$watch('address', function() {
		$scope.update();
	});


	// Diallog
	$scope.isAddressEditorOpen = false;
	$scope.open = function() {
		$scope.isAddressEditorOpen = true;
	};
	$scope.close = function() {
		$scope.update();
		$scope.isAddressEditorOpen = false;
	};
	$scope.save = function() {
		/*if (!$scope.item.country || !$scope.item.region || !$scope.item.city) {
			var title = 'Форма не заполнена';
			var msg = 'Необходимо заполнить все поля';
			var btns = [{
				result : 'ok',
				label : 'OK',
				cssClass : 'btn-primary'
			}];
			$dialog.messageBox(title, msg, btns).open();
			$scope.showMore = True;
			$scope.$digest();
			return;
		}*/
		if ($scope.item.is_new) {
			
			$scope.item.$save(function(obj) {
				$scope.address = obj.id;
				if($scope.$parent.address_class == 'Cemetery'){
					Cemetery.get({
						cemeteryID : $scope.$parent.cemetery.id
					}, function(result) {
						result.address = obj.id;
						result.$update();
						
						$scope.update();
						$scope.close();
					});
				}else{
					$scope.$parent.item.address = obj.id;
					$scope.$parent.item.$update({
						cemetery_id : $scope.$parent.address_class_params.cemetery_id,
						area_id : $scope.$parent.address_class_params.area_id,
						address_id : obj.id
					},function(){
						$scope.update();
						$scope.close();
					});
				}
			});
		} else {
			$scope.item.$update(function(obj) {
				$scope.update();
				$scope.close();
			});
		}
	};

	// EOF Diallog
}]);


app.directive('address', [
function() {
	return {
		restrict : 'EA',
        replace:true,
		controller : 'AddressController',
		require : 'address',
		templateUrl : STATIC_APP_URL + '/directive/address/address.html' + version_str,
		scope : {
			address : '=',
			address_class : '=',
			save_action : '&'
		},
		link : function($scope, elem, attr, addressCtrl) {
			// Address autopopulate 	
		    function completeCountry(event, ui) {
		    	var data = ui.item.value.split("/");  
		        $scope.item.country = data[0];
		        $(this).val($scope.item.country);
		        return false;
		    };
		    function completeRegion(event, ui) {
		        var data = ui.item.value.split("/");
		        $scope.item.country = data[1];
				$scope.item.region = data[0];
		        $(this).val($scope.item.region);
		        return false;
		    };
		    function completeCity(event, ui) {
		        var data = ui.item.value.split("/");
		        $scope.item.country = data[2];
				$scope.item.region = data[1];
				$scope.item.sity = data[0];
				$(this).val($scope.item.city);
		        return false;
		    };
		    function completeStreet(event, ui) {
		        var data = ui.item.value.split("/");
		        $scope.item.country = data[3];
				$scope.item.region = data[2];
				$scope.item.sity = data[1];
				$scope.item.street = data[0];
				$(this).val($scope.item.street);
		        return false;
		    };
			elem.find("input.country").autocomplete({
				source : function(term, callback) {
					var url = "/geo/autocomplete/country/?query=" + term.term;
					$.getJSON(url, function(data) {
						callback(data);
					});
				},
				minLength : 1,
				 delay : 100,
				 select: completeCountry,
				 focus: completeCountry
			});

			 elem.find("input.region").autocomplete({
		        source: function(term, callback) {
		            var url = "/geo/autocomplete/region/?query="+term.term;
		            with($scope.item)
		            	url += "&country=" + $scope.item.country;
		            $.getJSON(url, function(data) {
		                callback(data);
		            });
		        },
		        minLength: 2,
		        delay : 100,
		        select: completeRegion,
		        focus: completeRegion
		    });
		    
			 elem.find("input.city").autocomplete({
		        source: function(term, callback) {
		            var url = "/geo/autocomplete/city/?query="+term.term;
		            with($scope.item)
		            	url += "&region=" + region + "&country=" + country;
		            $.getJSON(url, function(data) {
		                callback(data);
		            });
		        },
		        minLength: 2,
		        delay : 100,
		        select: completeCity,
		        focus: completeCity
		    });		

		
		    elem.find("input.street").autocomplete({
		        source: function(term, callback) {
		            var url = "/geo/autocomplete/street/?query="+term.term;
		            with($scope.item)
		            	url += "&country=" + $scope.item.country + "&region=" + $scope.item.region + "&city=" + $scope.item.city;
		            $.getJSON(url, function(data) {
		                callback(data);
		            });
		        },
		        minLength: 2,
		        delay : 100,
		        select: completeStreet,
		        focus: completeStreet
		    });
		}
	};
}]);




