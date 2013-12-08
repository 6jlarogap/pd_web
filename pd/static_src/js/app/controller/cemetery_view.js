var qqq;//'use strict';
app.controller('CemeteryViewCtrl',
function CemeteryViewCtrl($scope, $http, $resource, $location,  $routeParams, 
						Cemetery, Area, AreaPurpose, Place, Phone, ymapData, naturalService) {
    "use strict";

	var tplButtonEdit = '<a class="btn btn-small" ng-href="/manage/cemetery/'+$routeParams.cemetery_id+
					'/area/{{row.getProperty(\'id\')}}">Открыть</a>',
					
		tplAvailability = '<span>{{row.getProperty(\'availability\')|list:AVAILABILITY_CHOICES}}</span>',
		tplPurpose = '<span>{{row.getProperty(\'purpose\')|objList:PURPOSE_LIST}}</span>',
		item = {
			address:false
		};
	$scope.area = {
		availability: 'open',
		purpose: 1,
		places_count:2
	};
	
	AreaPurpose.get(function(result) {
		$scope.PURPOSE_LIST = result;
	});
	
    $scope.gridOptions = { 
        data: '(area_list|filter:search)',
        enableRowSelection:false,
        columnDefs: [
        	{field: 'name', displayName: 'Наименование'},
        	{cellTemplate:tplAvailability, displayName: 'Открытость'},
        	{cellTemplate:tplPurpose, displayName: 'Назначение'},
        	{field: 'places_count', displayName: 'Кол-во могил в месте'},
            {displayName:'Действие',cellTemplate:tplButtonEdit}
        ]
    };

	$scope.PLACE_TYPES = PLACE_TYPES;	
	$scope.AVAILABILITY_CHOICES = AVAILABILITY_CHOICES;

	$scope.alerts = [];$scope.closeAlert = function(index){$scope.alerts.splice(index,1);};
	
	$scope.coordinates = false;
	$scope.update = function(){
		$scope.address_class = 'Cemetery';
		$scope.address_class_params ={
			cemeteryID : $routeParams.cemetery_id
		};
		Cemetery.getForm({cemeteryID:$routeParams.cemetery_id}, function(result) {
			if(result.status === 404){
	            $location.path('/manage/404');
                $location.replace();
		    }
			$scope.cemetery = new Cemetery(result.cemetery);
			$scope.address = result.address;
			$scope.cemetery.time_begin = new Date('0 '+ $scope.cemetery.time_begin);
			$scope.cemetery.time_end = new Date('0 '+ $scope.cemetery.time_end);
			
			$scope.phones = [];
			angular.forEach(result.phones, function(item) {
                  $scope.phones.push(new Phone(item));
            });

		});

		Area.list({cemetery_id: $routeParams.cemetery_id}, function(result) {
			$scope.area_list = result;
			$scope.area_list.sort(function(a,b){return naturalService.naturalSortField(a,b,'name')});
		});
		
		
		Place.list_cemetery({cemetery_id:$routeParams.cemetery_id},function(result) {
			var data = [];
			for(var i=0; i<result.length;i++){
				if(result[i].lng && result[i].lat){
					var title = "Кл. {0}, уч. {1}, ряд {2}, место {3}".format(
									($scope.cemetery && $scope.cemetery.name) || '',
			            			//'area.name',
			            			'?',
			            			result[i].row || DEFAULT_MESSAGES.no_data,
			            			result[i].place
			            		);
					data.push({
							id: result[i].id,
							point:[result[i].lat, result[i].lng],
							title:title,
							caption: 'Место: "{0}"'.format(result[i].place),
							content: title,

						});
				}
			}
			ymapData.markers = data;
			ymapData.points = [];
		    $scope.$broadcast('handleMapChanged');
		});
	};


	// Diallog
	$scope.opts = {
		backdropFade : true,
		dialogFade : true
	}; 
	$scope.isEditorOpen = false;
	$scope.openEditForm = function() {
		$scope.isEditorOpen = true;
		$('body').css('overflow-y','hidden');
	};
	$scope.closeEditForm = function() {
		$scope.isEditorOpen = false;
		$('body').css('overflow-y','auto');
		$scope.update();
	};
	$scope.saveEditForm = function() {
		$scope.cemetery.time_begin = date2time($scope.cemetery.time_begin);
		$scope.cemetery.time_end = date2time($scope.cemetery.time_end);
		$scope.cemetery.obj_phones = $scope.phones;
		$scope.cemetery.$update(function(){
			$scope.closeEditForm();
			$scope.update();
			noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
		});
	};
	
	// EOF Diallog


	// ADD form
	$scope.addModalOpened = false;
    $scope.optsModal = {
        backdrop: true,
        keyboard: true,
        backdropClick: true,
    };
  
    $scope.openAddModal = function () {
        $scope.addModalOpened = true;
        $('body').css('overflow-y','hidden');
    };

    $scope.closeAddModal = function () {
        $scope.addModalOpened = false;
        $('body').css('overflow-y','auto');
        $scope.update();
    };
	$scope.addElement = function(){
		$scope.area.cemetery = $routeParams.cemetery_id;
		var newArea = new Area($scope.area);
		newArea.$save({cemetery_id: $routeParams.cemetery_id}, function(result){
			$scope.closeAddModal();
   			$location.path('/manage/cemetery/'+$routeParams.cemetery_id+'/area/'+result.id);
   			$location.replace();
        });
	};
	// EOF ADD form



	// RUN
	$scope.$on("$routeChangeSuccess",function(event){
		$scope.update();
	});

	// set default map data
	ymapData.markers = [];
	ymapData.points = [];
    $scope.$broadcast('handleMapChanged');
});