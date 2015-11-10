'use strict';

function CemeteryCtrl($rootScope, $scope, $http, $location, $resource, naturalService, Cemetery, CemeteryEditors) {

    "use strict";
    var object_url = '/api/cemetery';
    $scope.cemetery_list = [];
    $scope.version_str = version_str;
    $scope.editor = {};

    var tplButtonEdit = '<a class="btn btn-small" ng-href="/manage/cemetery/{{row.getProperty(\'id\')}}">Открыть</a>';
    var tplLinkOpen = '<a ng-class="col.colIndex()" ng-href="/manage/cemetery/{{row.getProperty(\'id\')}}">{{row.getProperty(\'name\')}}</a>';
    $scope.search = {name:''};
    $scope.gridOptions = { 
        data: 'cemetery_list',
        enableRowSelection:false,
        columnDefs: [
            {field: 'name', cellTemplate:tplLinkOpen, displayName:'Наименование'},
            {field: 'work_time', displayName: 'Часы работы'},
            {field: 'area_cnt', displayName: 'Участков'},
            {displayName:'Действие',cellTemplate:tplButtonEdit}
        ],
        showFilter: true
    };

    $scope.alerts = [];$scope.closeAlert = function(index){$scope.alerts.splice(index,1);};
    
    $scope.update = function() {
        $scope.editor.cemetery = new Cemetery({
                // любые правильные даты с временами по умолчанию начала и окончания работы
                time_begin: new Date(2000, 1, 1, 8, 0, 0),
                time_end: new Date(2000, 1, 1, 17, 0, 0),
                places_algo:'manual',
                places_algo_archive:'manual',
                time_slots:'',
                archive_burial_fact_date_required:false,
                archive_burial_account_number_required:false
            });
        Cemetery.canAddCemetery(
                    {cemeteryID:0}, // fake cemetery id to find out if the user may add cemetery
                    function(result) {
           $scope.can_add_cemetery = result.can_add_cemetery; 
        });
        Cemetery.query(function(result) {
            $scope.cemetery_list = result;
            $scope.cemetery_list.sort(function(a,b){return naturalService.naturalSortField(a,b,'name')});
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
        $scope.update();
    };
    $scope.addElement = function(){
        $scope.editor.cemetery.time_begin = date2time($scope.editor.cemetery.time_begin);
        $scope.editor.cemetery.time_end = date2time($scope.editor.cemetery.time_end);

        $scope.editor.cemetery.$save(function(result){
            $scope.closeAddModal();
            $location.path('/manage/cemetery/'+result.id);
            $location.replace();
        }, default_display_response_error);
    };
    // EOF ADD form


    // RUN
    $scope.$on("$routeChangeSuccess",function(event){
        $scope.update();
    });
    $scope.$watch(function () {
        return $scope.editor.cemetery ? $scope.editor.cemetery.places_algo_archive : null;
    }, function (placesAlgoArchive, oldPlacesAlgoArchive) {
        if (placesAlgoArchive !== oldPlacesAlgoArchive && 'burial_account_number' === placesAlgoArchive) {
            $scope.editor.cemetery.archive_burial_account_number_required = true;
        }
    });
}
