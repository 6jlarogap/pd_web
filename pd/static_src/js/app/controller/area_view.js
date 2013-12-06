//'use strict';

function AreaViewCtrl($scope, $rootScope, $http, $routeParams, $resource, $location, Cemetery, Area, AreaPhoto,
	AreaPurpose, uploadManager, Place) {

    "use strict";
	var tplButtonEdit = '<a class="btn btn-small" ng-href="/manage/cemetery/'+$routeParams.cemetery_id+
					'/area/'+$routeParams.area_id+'/place/{{row.getProperty(\'id\')}}">Открыть</a>';
	var tplFIO = '<div>{{row.getProperty(\'responsible.last_name\')}} {{row.getProperty(\'responsible.first_name\')}} {{row.getProperty(\'responsible.middle_name\')}}</div>';


	$scope.place = {
		row :'',
		place : '',
		cemetery: $routeParams.cemetery_id,
		area: $routeParams.area_id
	};
	$scope.AVAILABILITY_CHOICES = AVAILABILITY_CHOICES; 



	$scope.alerts = [];$scope.closeAlert = function(index){$scope.alerts.splice(index,1);};
	
	$scope.area_photo = [];
	$scope.currentImage = false;


	AreaPurpose.get(function(result) {
		$scope.PURPOSE_LIST = result;
	});


	$scope.update = function(){

		Area.get({areaID:$routeParams.area_id,  cemetery_id: $routeParams.cemetery_id}, function(area) {
			if(!area.id)
				window.location = '/manage/500?title=Участок не найден';
			$scope.area = area;
	        AreaPhoto.query({area_id:area.id}, function(photo){
	            $scope.area_photo = photo;
	            $scope.currentImage = photo[0];
	        });
		});
		Cemetery.get({cemeteryID:$routeParams.cemetery_id}, function(result) {
		    $scope.cemetery = result;
		});
		Place.query({
			 	cemetery_id: $routeParams.cemetery_id, 
				area_id: $routeParams.area_id
			}, function(result) {
			$scope.place_list = result;
			$scope.place_list.sort();
			try{
				$scope.$digest();
			}catch(e){}
		});
	};

    $scope.setCurrentImage = function (image) {
        $scope.currentImage = image;
    };

    $scope.gridOptions = { 
        data: '(place_list|filter:search)',
        enableRowSelection:false,
        columnDefs: [
        	{field: 'row', displayName: 'Ряд'},
        	{field: 'place', displayName: 'Место'},
        	{displayName:'Ответственный', field:'responsible_txt'}, 
            {displayName:'Действие',cellTemplate:tplButtonEdit}
        ]
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
	};
	$scope.saveEditForm = function() {
		$scope.area.cemetery_id = $routeParams.cemetery_id;
		$scope.area.$update({cemetery_id: $routeParams.cemetery_id}, function(){
			$scope.closeEditForm();
			$scope.update();
			noty({text: 'Элемент сохранен', type:'success', layout:'topRight'});
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
    };
	$scope.addElement = function(){
		$scope.closeAddModal();
		var place = new Place($scope.place);
		place.$save({area_id:$routeParams.area_id}, function(result){
			var url = '/manage/cemetery/{0}/area/{1}/place/{2}'.format($routeParams.cemetery_id, $routeParams.area_id, result.id);
			$location.path(url);
   			$location.replace();
  		});
	};
	// EOF ADD form


	// Galery add dialog
	$scope.gallery_data = {
				area:$routeParams.area_id
			};
	$scope.gallery_url = '/api/area-photo?format=json';
	
	$scope.csrfToken = csrfToken;
	$scope.uploadImageModalOpened = false;
	$scope.openUploadImageModal = function() {
	    $scope.default_lat = (ymaps && ymaps.geolocation && ymaps.geolocation.latitude) || '';
	    $scope.default_lng = (ymaps && ymaps.geolocation && ymaps.geolocation.longitude) || '';
		$scope.uploadImageModalOpened = true;
	};
	$scope.closeUploadImageModal = function() {
		$scope.uploadImageModalOpened = false;
	};
	// EOF Galery add dialog


   // File Upload
    $scope.files = [];
    $scope.percentage = 0;

    $scope.upload = function () {
        uploadManager.upload($scope.gallery_data);
        // TODO: retriew new object and set lat, lng, comment
        $scope.files = [];
        return false;
    };
    $scope.clear = function () {
        uploadManager.clear();
        $scope.files = [];
        return false;
    };
    $rootScope.$on('fileAdded', function (e, call) {
        $scope.files.push(call);
        $scope.$apply();
    });

    $rootScope.$on('uploadProgress', function (e, call) {
        $scope.percentage = call;
        $scope.$apply();
    });
   // EOF File Upload


	// RUN
	$scope.$on("$routeChangeSuccess",function(event){
		$scope.update();
	});
}
