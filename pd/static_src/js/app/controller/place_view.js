app.controller('PlaceViewCtrl', function PlaceViewCtrl($scope, $routeParams, $location, 
	Place, Cemetery, Grave, GravePhoto, Burial, Area, AlivePerson, Phone, Log, ymapData, $dialog) {
	"use strict";

	//Constants
	//todo put all constants in constant provider
	$scope.BURIAL_CONTAINERS = BURIAL_CONTAINERS;
	$scope.BURIAL_TYPES = BURIAL_TYPES;
	$scope.STATUS_CHOICES = STATUS_CHOICES;

	$scope.logGridOptions = {
		data : 'place_log',
		enableRowSelection : false,
		columnDefs : [
			{
				field : 'dt',
				displayName : 'Дата',
				width:'130'
			}, {
				field : 'user',
				displayName : 'Пользователь',
				width:'250'
			}, {
				field : 'msg',
				displayName : 'Действие'
			}
		]
	};

	//setup
	$scope.updateMap = function() {
		ymapData.markers = [{
				point: [$scope.item.lat, $scope.item.lng],
				caption: 'Место: "{0}"'.format($scope.item.place),
				content: "Кл. {0}, уч. {1}, ряд {2}, место {3}".format(
														$scope.cemetery.name, 
														$scope.area.name, 
														$scope.item.row || DEFAULT_MESSAGES.no_data, 
														$scope.item.place),

				obj_type : 'place',
				id: $scope.item.id
			}];
		$scope.placeCoordinates = [{
			point : [$scope.item.lat, $scope.item.lng],
			title : $scope.item.name,
			obj_type : 'place',
			id: $scope.item.id
		}];
		ymapData.points = [];
		angular.forEach($scope.graves, function(grave, key) {
			if (grave.lat && grave.lng) {
				ymapData.points.push({
					point : [grave.lat, grave.lng],
					caption : 'Могила {0}'.format(grave.grave_number),
					content : '',
					obj_type : 'grave',
					id: grave.pk
				});
			}
		});
		$scope.$broadcast('handleMapChanged');
	};

	$scope.update = function() {
		Log.place_log({id:$routeParams.place_id},function(result) {
			$scope.place_log = result;
		});
		var item_params = {
			placeID : $routeParams.place_id,
			cemetery_id : $routeParams.cemetery_id,
			area_id : $routeParams.area_id
		};
		$scope.address_class = 'Place';
		$scope.address_class_params = item_params;


		Place.getForm(item_params, function(result) {
			
			$scope.cemetery = new Cemetery(result.cemetery);
			$scope.area = new Area(result.area);
			$scope.item = new Place(result.place);
			
			$scope.responsible_phones = [];
			angular.forEach(result.responsible_phones, function(item) {
                  $scope.responsible_phones.push(new Phone(item));
            });

			//$scope.burials = new Burial(result.burials);
			//$scope.graves = new Grave(result.graves);
			
			if(result.responsible){
				$scope.responsible = new AlivePerson(result.responsible);
			}else{
				$scope.responsible = new AlivePerson({
					is_new : true
				});
			}

			$scope.item.name = "Кл. {0}, уч. {1}, ряд {2}, место {3}".format($scope.cemetery.name, $scope.area.name, $scope.item.row || DEFAULT_MESSAGES.no_data, $scope.item.place)
			$scope.updateGraves();
		},function(data){
			if(data.status==404){
				window.location = '/manage/404?title=Место не найдено';
			}
		});
		
	};

	$scope.updateGraves = function() {
		Grave.query({
			place_id : $routeParams.place_id
		}, function(graves) {
			$scope.max_grave_number = graves.length;
			$scope.graves = graves;

			
			$scope.updateMap(); 
		    
			angular.forEach($scope.graves, function(grave, key) {
				GravePhoto.query({
					grave_id : grave.id
				}, function(photos) {
					if (!_.isEmpty(photos)) {
						grave.photos = photos;
						grave.firstPhoto = _.first(photos).bfile;
					}
				});
			});
		    
			// New element with default data
			$scope.newGrave = new Grave({
				place : $scope.item.id,
				grave_number : $scope.graves.length + 1, //todo add way to count next grave_number or add validation of grave_number
				//lat: lat || 0,
				//lng: lng || 0
			});
		});
		Burial.query({
			cemetery_id : $routeParams.cemetery_id,
			area_id : $routeParams.area_id,
			place_id : $routeParams.place_id
		}, function(result) {
			$scope.burials = result;
		});
	};

	//alerts
	$scope.alerts = [];
	$scope.closeAlert = function(index) {
		$scope.alerts.splice(index, 1);
	};
	//$scope.alerts.push({msg: "Another alert!"});

	//todo extrude place and burial edit in separate controllers with tpl
	// Diallog
	$scope.opts = {
		backdropFade : true,
		dialogFade : true
	};

	$scope.openEditForm = function(form, data) {
		$scope[form] = true;
		$('body').css('overflow-y','hidden');
		switch (form) {
			case 'isBurialEditorOpen':
				if (data) {
					Burial.get({
						cemetery_id : $routeParams.cemetery_id,
						area_id : $routeParams.area_id,
						place_id : $routeParams.place_id,
						burialID : data.id
					}, function(result) {
						result.plan_time = result.plan_time || '';
						$scope.selectedBurial = result;
					});
				}
				break;
			case 'isGraveAddOpen':
				if ($scope.placeCoordinates) {
					var lat = $scope.placeCoordinates.lat, lng = $scope.placeCoordinates.lng;
				}
				$scope.newGrave = new Grave({
					place : $scope.item.id,
					grave_number : $scope.graves.length + 1, //todo add way to count next grave_number or add validation of grave_number
					lat : lat || 0,
					lng : lng || 0
				});
				break;
			case 'isGraveEditOpen':
				if (data) {
					$scope.selectedGrave = data;
					$scope.originGraveNumber = data.grave_number;
				}
				break;
			case 'isGraveGalleryOpen':
				if (data) {
					$scope.selectedGravePhotos = data;
					$scope.setCurrentImage(_.first(data));
				}
				break;
		}
	};

	$scope.setCurrentImage = function(image) {
		$scope.currentImage = image;
	};

	$scope.closeEditForm = function(form) {
		$scope[form] = false;
		$('body').css('overflow-y','auto');
	};

	//Place
	$scope.isPlaceEditorOpen = false;
	$scope.savePlaceEditForm = function(form) {
		if (form.$valid) {
			var url = '/manage/cemetery/{0}/area/{1}/place/{2}'.format($scope.item.cemetery, $scope.item.area, $scope.item.id);
			$scope.item.$update({
				cemetery_id : $routeParams.cemetery_id,
				area_id : $routeParams.area_id
			}, function() {
				$scope.updateMap();
				$scope.closeEditForm('isPlaceEditorOpen');
				noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
				$location.path(url);
				$location.replace();
				//$scope.update();
			});
		}
	};

	//Responsible
	$scope.isResponsibleEditorOpen = false;
	$scope.saveResponsibleEditForm = function(form) {
		if (form.$valid || true) { //TODO: check this
			$scope.item.obj_responsible = $scope.responsible;
			$scope.item.obj_responsible_phones = $scope.responsible_phones; 
			
			$scope.item.$update({
				cemetery_id : $routeParams.cemetery_id,
				area_id : $routeParams.area_id
			}, function() {
				noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
				$scope.update();
			});

			/*if ($scope.responsible.is_new) {
				$scope.responsible.$save(function(data) {
					$scope.item.responsible = data.id;
					$scope.item.$update({placeID : $routeParams.place_id,
										cemetery_id : $routeParams.cemetery_id,
										area_id : $routeParams.area_id
					},function() {
						noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
						$scope.update();
					});
				});
			} else {
				$scope.responsible.$update(function() {
					$scope.update();
					noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
				});
			}*/
			
			
			$scope.closeEditForm('isResponsibleEditorOpen');
		}
	};

	$scope.removeResponsible = function() {
		if ($scope.responsible.last_name || $scope.responsible.first_name || $scope.responsible.middle_name) {
			var fio = "{0} {1} {2}".format($scope.responsible.last_name, $scope.responsible.first_name, $scope.responsible.middle_name);
			if (confirm("Открепить " + fio + '?')) {
				delete $scope.item.responsible;
				$scope.item.$update({placeID : $routeParams.place_id,
										cemetery_id : $routeParams.cemetery_id,
										area_id : $routeParams.area_id
					},function() {
					noty({text: fio + " откреплен.", type:'success', layout:'topRight'});
					$scope.update();
				});
			}
		}
	};

	$scope.onCemeteryChanged = function($item, $model) {
		if ($item) {
			Area.query({
				cemetery_id : $item.id
			}, function(result) {
				$scope.area_list = result;
			});

			$scope.area = undefined;
			$scope.cemetery = $item;
		}
	};

	$scope.onAreaChanged = function($item, $model, $value) {
		if ($item) {
			$scope.area = $item;
		}
	};

	//Grave
	
	$scope.graveMove = function(direction, grave){
		grave.$move({
				cemetery_id : $routeParams.cemetery_id,
				area_id : $routeParams.area_id,
				place_id : $routeParams.place_id,
				graveID:grave.id,
				direction:direction
			},function(data){
				$scope.update();
			});
	};

	$scope.isGraveAddOpen = false;

	$scope.addGrave = function(form) {
		if (form.$valid) {
			$scope.newGrave.$save(function() {
				$scope.closeEditForm('isGraveAddOpen');
				$scope.updateGraves();
				var msg = "Могила добавлена.";
				noty({text: msg, type:'success', layout:'topRight'});
				$scope.update();
			});
		}
	};

	$scope.isGraveEditOpen = false;
	$scope.saveGraveEditForm = function(form) {
		if (form.$valid) {
			var graveUpdateHandler = function() {
				$scope.closeEditForm('isGraveEditOpen');
				$scope.updateGraves();
				var msg = "Изменения сохранены.";
				noty({text: msg, type:'success', layout:'topRight'});
			};

			var targetGrave = _.find($scope.graves, function(grave) {
				return grave.grave_number == $scope.selectedGrave.grave_number && grave.id !== $scope.selectedGrave.id;
			});

			if (targetGrave) {
				targetGrave.grave_number = $scope.originGraveNumber;
			}

			$scope.selectedGrave.$update(function(targetGrave) {
				if (targetGrave) {
					targetGrave.$update(graveUpdateHandler);
				} else {
					graveUpdateHandler();
				}
				$scope.update();
			});
		}
	};

	$scope.deleteGrave = function(grave) {
		
        var title = 'Подтверждение удаления',
            msg = 'Все прикрепленные фотографии также будут удалены',
            btns = [ {result:'ok', label: 'Удалить'},
            		 {result:'cancel', label: 'Отмена', cssClass: 'btn-primary'}];
        $scope.grave_to_delete = grave;
        $dialog.messageBox(title, msg, btns)
               .open()
               .then(function(result){
					if (result=='ok') {
						//var grave = new Grave($scope.grave_to_delete);
						$scope.grave_to_delete.$delete(function(){
							$scope.updateGraves();
							var msg = "Могила удалена.";
							noty({text: msg, type:'success', layout:'topRight'});
							delete $scope.grave_to_delete;
							$scope.update();
						});
					}
               });
	};

	$scope.haveBurials = function(graveID) {
		return _.any($scope.burials, function(burial) {
			return burial.grave === graveID;
		});
	};

	$scope.isGraveGalleryOpen = false;

	//Burial
	$scope.isBurialEditorOpen = false;
	$scope.saveBurialEditForm = function(form) {
		if (form.graveNumber.$dirty && form.$valid) {
			$scope.selectedBurial.grave_number = $scope.selectedBurial.grave.grave_number;
			$scope.selectedBurial.grave = $scope.selectedBurial.grave.id;
			$scope.selectedBurial.$update({
				cemetery_id : $routeParams.cemetery_id,
				area_id : $routeParams.area_id,
				place_id : $routeParams.place_id
			},function() {
				$scope.closeEditForm('isBurialEditorOpen');
				$scope.updateGraves();
				var msg = "Изменения сохранены.";
				noty({text: msg, type:'success', layout:'topRight'});
			});
		}
	};
	// EOF Diallog

	// RUN
	$scope.$on("$routeChangeSuccess", function(event) {
		$scope.update();
	});

	$scope.$on("mapPointChanged:place", function(event, data) {
		if($scope.item.id == data.obj_id){
			$scope.item.lat = data.coords[0];
			$scope.item.lng = data.coords[1];
			$scope.$digest();
			$scope.item.$update({
				cemetery_id : $routeParams.cemetery_id,
				area_id : $routeParams.area_id
			},function(data){
				$scope.update();
			});
		}
	});

	ymapData.markers = [];
	ymapData.points = [];
    $scope.$broadcast('handleMapChanged');

});
