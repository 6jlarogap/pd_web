//'use strict';
app.controller('CemeteryViewCtrl',
function CemeteryViewCtrl($scope, $http, $resource, $location,  $routeParams, 
						Cemetery, Area, AreaPurpose, Place, Phone, Address, ymapData, naturalService) {
    "use strict";
    $scope.version_str = version_str;
	var tplButtonEdit = '<a class="btn btn-small" ng-href="/manage/cemetery/'+$routeParams.cemetery_id+
					'/area/{{row.getProperty(\'id\')}}">Открыть</a>',
					
		tplAvailability = '<span>{{row.getProperty(\'availability\')|list:AVAILABILITY_CHOICES}}</span>',
		tplPurpose = '<span>{{row.getProperty(\'purpose\')|objList:PURPOSE_LIST}}</span>',
		item = {
			address:false
		};

	$scope.editor = {
			isAddressEdited: false,
			isPhoneEdited: false,
			isEditorOpen: false
	};
	$scope.area_max_places = 10;
    $scope.gridOptions = { 
        data: 'area_list|filter:search',
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

	AreaPurpose.get(function(result) {
		$scope.PURPOSE_LIST = result;
	});
	
	$scope.alerts = [];$scope.closeAlert = function(index){$scope.alerts.splice(index,1);};
	
	$scope.coordinates = false;
	$scope.update = function(){
	    $scope.area = {
	            availability: 'open',
	            purpose: 1,
	            places_count:1
	        };
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
			$scope.cemetery.time_begin = new Date('0 '+ $scope.cemetery.time_begin);
			$scope.cemetery.time_end = new Date('0 '+ $scope.cemetery.time_end);
			
			$scope.phones = [];
			angular.forEach(result.phones, function(item) {
                  $scope.phones.push(new Phone(item));
            });


			$scope.cemetery_address = new Address(result.address);
			if(!$scope.cemetery_address.region)
				$scope.cemetery_address.region = {};
			if(!$scope.cemetery_address.country)
				$scope.cemetery_address.country = {};
			if(!$scope.cemetery_address.city)
				$scope.cemetery_address.city = {};
			if(!$scope.cemetery_address.street)
				$scope.cemetery_address.street = {};

		});

		Area.list({cemetery_id: $routeParams.cemetery_id}, function(result) {
			$scope.area_list = result;
			$scope.area_list.sort(function(a,b){return naturalService.naturalSortField(a,b,'name')});
		});
	};


	// Diallog
	$scope.opts = {
		backdropFade : true,
		dialogFade : true
	}; 
	$scope.isEditorOpen = false;
	$scope.openEditForm = function() {
		$scope.editor.isEditorOpen = true;
		$scope.editor.isAddressEdited =  false;
		$scope.editor.isPhoneEdited = false;
		$('body').css('overflow-y','hidden');
	};
	$scope.closeEditForm = function() {
		$scope.editor.isEditorOpen = false;
		$('body').css('overflow-y','auto');
		$scope.update();
	};
	$scope.saveEditForm = function() {
		$scope.cemetery.time_begin = date2time($scope.cemetery.time_begin);
		$scope.cemetery.time_end = date2time($scope.cemetery.time_end);
		$scope.cemetery.obj_phones = $scope.phones;
		$scope.cemetery.obj_address = $scope.cemetery_address;
		$scope.cemetery.$update(function(){
			$scope.closeEditForm();
			$scope.update();
			noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
		}, default_display_response_error);
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
        }, default_display_response_error);
	};
	// EOF ADD form

	$scope.is_editor_disabled = function(form){
		var o = $scope.editor;
		var form1_valid = form.$valid,
			  form2_valid = o.isAddressValid===true,
			  form3_valid = $scope.phones && $scope.phones.length>0;
		return !(   
						!(o.isAddressEdited || o.isPhoneEdited) &&
						form1_valid //&& (form2_valid || form3_valid) 
					);
	};


	// RUN
	$scope.$on("$routeChangeSuccess",function(event){
		$scope.update();
	});

	// set default map data
	ymapData.markers = [];
	ymapData.points = [];
    $scope.$broadcast('handleMapChanged');
});