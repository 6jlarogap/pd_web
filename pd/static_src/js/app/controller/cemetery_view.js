//'use strict';
app.controller('CemeteryViewCtrl',
function CemeteryViewCtrl(
        $scope, $http, $resource, $location,  $routeParams, 
        Cemetery, Area, AreaPurpose, Place, Phone, Address, ymapData, naturalService, pdYandex, CemeteryEditors) {

    "use strict";
    $scope.version_str = version_str;
    var tplButtonEdit = '<a class="btn btn-small" ng-href="/manage/cemetery/'+$routeParams.cemetery_id +
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
        data: 'area_list',
        enableRowSelection:false,
        columnDefs: [
            {field: 'name', displayName: 'Наименование'},
            {cellTemplate:tplAvailability, displayName: 'Открытость'},
            {cellTemplate:tplPurpose, displayName: 'Назначение'},
            {field: 'places_count', displayName: 'Кол-во могил в месте'},
            {displayName:'Действие',cellTemplate:tplButtonEdit}
        ],
        showFilter: true
  };

    $scope.PLACE_TYPES = PLACE_TYPES;
    $scope.PLACE_ARCHIVE_TYPES = PLACE_ARCHIVE_TYPES;
    $scope.AVAILABILITY_CHOICES = AVAILABILITY_CHOICES;

    AreaPurpose.get(function(result) {
        $scope.PURPOSE_LIST = result;
    });

    $scope.alerts = [];$scope.closeAlert = function(index){$scope.alerts.splice(index,1);};

    $scope.coordinates = false;

    $scope.updateMap = function () {
        if ($scope.cemetery) {
            var latitude = null;
            var longitude = null;
            var caption = 'Кладбище: "{0}"'.format($scope.cemetery.name);
            if ($scope.cemetery &&
                $scope.cemetery_address &&
                $scope.cemetery_address.gps_y &&
                $scope.cemetery_address.gps_x) {
                    latitude = $scope.cemetery_address.gps_y;
                    longitude = $scope.cemetery_address.gps_x;
                }
            ymapData.markers = [
                {
                    point: [
                        geo.getLat(latitude),
                        geo.getLng(longitude)
                    ],
                    caption: caption,
                    content: caption,
                    obj_type: 'cemetery',
                    id: $scope.cemetery.id
                }
            ];
            $scope.cemeteryMapZoom = 14;
            $scope.cemeteryCoordinates = [
                {
                    point: [
                        geo.getLat(latitude),
                        geo.getLng(longitude)
                    ],
                    title: caption,
                    obj_type: 'cemetery',
                    id: $scope.cemetery.id
                }
            ];
        } else {
            ymapData.markers = [];
        }
        ymapData.points = [];
        $scope.$broadcast('handleMapChanged');
    };

  $scope.$on("mapPointChanged:cemetery", function (event, data) {
    if ($scope.cemetery.id == data.obj_id) {
        var message = !$scope.cemetery_address.gps_x &&
                      typeof($scope.cemetery_address.gps_x) === "object" ?
                        // is null
                        "Задать координаты кладбища?" :
                        "Изменить координаты кладбища?";
         if (confirm(message)) {
                $scope.cemetery.obj_address = $scope.cemetery_address;
                $scope.cemetery.obj_address.gps_x = data.coords[1];
                $scope.cemetery.obj_address.gps_y = data.coords[0];
                $scope.cemetery.time_begin = date2time($scope.cemetery.time_begin);
                $scope.cemetery.time_end = date2time($scope.cemetery.time_end);
                $scope.$digest();
                $scope.cemetery.$update(function() {
                    $scope.update();
                    noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
                });
         }
        ymapData.map.setCenter(data.coords);
    }
  });

    $scope.update = function() {
        $scope.area = {
            availability: 'open',
            purpose: 1,
            places_count: 1
        };
        $scope.address_class = 'Cemetery';
        $scope.address_class_params = {
            cemeteryID : $routeParams.cemetery_id
        };
        Cemetery.getForm({cemeteryID:$routeParams.cemetery_id}, function(result) {
            if(result.status === 404){
                $location.path('/manage/404');
                $location.replace();
            }

            $scope.cemetery = new Cemetery(result.cemetery);
            $scope.is_editable = result.is_editable;
            $scope.can_add_area = result.can_add_area;
            $scope.editor.caretaker = result.cemetery.caretaker;
            $scope.editor.caretakers = result.caretakers;
            
            $scope.caretaker_show = caretakerShow(
                result.cemetery.caretaker,
                result.caretakers
            );
            $scope.cemetery.time_begin = moment($scope.cemetery.time_begin, 'HH:mm:ss').toDate();
            $scope.cemetery.time_end = moment($scope.cemetery.time_end, 'HH:mm:ss').toDate();

            $scope.phones = [];
            angular.forEach(result.phones, function(item) {
                $scope.phones.push(new Phone(item));
            });

            $scope.cemetery_address = new Address(result.address);
            if(!$scope.cemetery_address.region) {
                $scope.cemetery_address.region = {};
            }
            if(!$scope.cemetery_address.country) {
                $scope.cemetery_address.country = {};
            }
            if(!$scope.cemetery_address.city) {
                $scope.cemetery_address.city = {};
            }
            if(!$scope.cemetery_address.street) {
                $scope.cemetery_address.street = {};
            }

            $scope.updateMap();
         });

        Area.list({cemetery_id: $routeParams.cemetery_id}, function(result) {
            $scope.area_list = result;
            $scope.area_list.sort(function(a,b){return naturalService.naturalSortField(a,b,'name')});
        });
    }; // end of scope.update function

    // Dialog
    $scope.opts = {
        backdropFade : true,
        dialogFade : true
    };
    $scope.isEditorOpen = false;
    $scope.openEditForm = function() {
        $scope.editor.isEditorOpen = true;
        $scope.editor.isAddressEdited =  false;
        $scope.editor.isPhoneEdited = false;
        $scope.editor.cemetery = angular.copy($scope.cemetery);
        $scope.editor.phones = angular.copy($scope.phones);
        $scope.editor.cemetery_address = angular.copy($scope.cemetery_address); 

        Cemetery.authData(
                    {cemeteryID: $scope.cemetery.id},
                    function(result) {
            $scope.ugh_registrators = result.ugh_registrators; 
            $scope.editor.cemetery_editors = [];
            $scope.cemetery_editors_pks = result.cemetery_editors_pks;
            for (var i=0; i< $scope.ugh_registrators.length; i++) {
                if ($scope.cemetery_editors_pks.indexOf($scope.ugh_registrators[i].id) >= 0) {
                    $scope.editor.cemetery_editors.push($scope.ugh_registrators[i]);
                }
            }
            $scope.select_users_size = Math.min($scope.ugh_registrators.length + 1, 10);
        });

        $('body').css('overflow-y','hidden');
    };

    $scope.closeEditForm = function() {
        $scope.editor.isEditorOpen = false;
        $('body').css('overflow-y','auto');
        $scope.update();
    };

    $scope.saveEditForm = function() {
        $scope.editor.cemetery.time_begin = date2time($scope.editor.cemetery.time_begin);
        $scope.editor.cemetery.time_end = date2time($scope.editor.cemetery.time_end);
        $scope.editor.cemetery.obj_phones = $scope.editor.phones;
        $scope.editor.cemetery.obj_address = $scope.editor.cemetery_address;
        $scope.editor.cemetery.caretaker = $scope.editor.caretaker;
        $scope.cemetery_editors_pks = [];
        for (var i=0; i < $scope.editor.cemetery_editors.length; i++) {
            $scope.cemetery_editors_pks.push($scope.editor.cemetery_editors[i].id);
        }
        $scope.editor.cemetery.$update(function(){
            CemeteryEditors.update({
                cemetery_id: $scope.cemetery.id,
                cemetery_editors_pks:$scope.cemetery_editors_pks
            }, function(result) {
            });
            $scope.closeEditForm();
            $scope.update();
            noty({text: 'Изменения сохранены', type:'success', layout:'topRight'});
        }, default_display_response_error);
    };
    // end of Dialog


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
    // end of ADD form

    $scope.is_editor_disabled = function(form){
        var o = $scope.editor;
        var form1_valid = form.$valid,
            form2_valid = o.isAddressValid === true,
            form3_valid = $scope.phones && $scope.phones.length > 0;
        return !(
            !(o.isAddressEdited || o.isPhoneEdited) &&
              form1_valid //&& (form2_valid || form3_valid)
            );
    };

    $scope.$watch(function () {
        return $scope.editor.cemetery ? $scope.editor.cemetery.places_algo_archive : null;
    },
    function (placesAlgoArchive, oldPlacesAlgoArchive) {
        if (placesAlgoArchive !== oldPlacesAlgoArchive && 'burial_account_number' === placesAlgoArchive) {
            $scope.editor.cemetery.archive_burial_account_number_required = true;
        }
    });

    // RUN
    $scope.$on("$routeChangeSuccess",function(event){
        $scope.update();
    });

    // set default map data
    ymapData.markers = [];
    ymapData.points = [];
    $scope.$broadcast('handleMapChanged');
});
