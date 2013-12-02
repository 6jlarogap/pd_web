'use strict';

function CemeteryCtrl($scope, $http, $location, $resource) {
    "use strict";
	var object_url = '/api/cemetery';
    $scope.cemetery_list = [];
	$scope.cemetery = {
		time_begin: new Date('0 8:00'),
		time_end: new Date('0 17:00'),
		places_algo:'area',
		time_slots:''
	};

	var Cemetery = $resource('/api/cemetery/:cemeteryID', {cemeteryID:'@id'},{});

	var tplButtonEdit = '<a class="btn btn-small" ng-href="/manage/cemetery/{{row.getProperty(\'id\')}}">Открыть</a>';
	var tplLinkOpen = '<a ng-class="col.colIndex()" ng-href="/manage/cemetery/{{row.getProperty(\'id\')}}">{{row.getProperty(\'name\')}}</a>';
    $scope.gridOptions = { 
        data: '(cemetery_list|filter:search| orderBy:natural("name"))',
        enableRowSelection:false,
        columnDefs: [
        	{field: 'name', cellTemplate:tplLinkOpen, displayName:'Наименование'},
        	{field: 'work_time', displayName: 'Часы работы'},
        	{field: 'area_cnt', displayName: 'Участков'},
            {displayName:'Действие',cellTemplate:tplButtonEdit}
        ]
    };
	
	
  $scope.alerts = [];$scope.closeAlert = function(index){$scope.alerts.splice(index,1);};
    
    $scope.update = function() {
		Cemetery.query(function(result) {
			$scope.cemetery_list = result;
		});

    };

	// ADD form
	$scope.addModalOpened = false;
    $scope.optsModal = {
        backdrop: true,
        keyboard: true,
        backdropClick: true,
    };
  
    $scope.openAddModal = function () {
		$('body').css('overflow-y','hidden');
        $scope.addModalOpened = true;
    };

    $scope.closeAddModal = function () {
        $scope.addModalOpened = false;
		$('body').css('overflow-y','auto');
    };
	$scope.addElement = function(){
		var data = {
				name:$scope.cemetery.name,
				places_algo: $scope.cemetery.places_algo,
				time_begin: date2time($scope.cemetery.time_begin),
				time_end:   date2time($scope.cemetery.time_end)
			};
		var newCemetery = new Cemetery(data);
		newCemetery.$save(function(result){
			$scope.closeAddModal();
   			$location.path('/manage/cemetery/'+result.id);
   			$location.replace();
        });
	};
	// EOF ADD form
	

	// RUN
	$scope.$on("$routeChangeSuccess",function(event){
		$scope.update();
	});

}
