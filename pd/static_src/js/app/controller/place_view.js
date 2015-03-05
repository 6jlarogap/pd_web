app.controller('PlaceViewCtrl', function PlaceViewCtrl($scope, $routeParams, $location, Place, Cemetery, Grave, Burial, Area, AlivePerson, Phone, Address, Log, ymapData, $dialog) {
  "use strict";

  //Constants
  //todo put all constants in constant provider
  $scope.version_str = version_str;
  $scope.BURIAL_CONTAINERS = BURIAL_CONTAINERS;
  $scope.BURIAL_TYPES = BURIAL_TYPES;
  $scope.STATUS_CHOICES = STATUS_CHOICES;
  $scope.BURIAL_STATUS_EXHUMATED = BURIAL_STATUS_EXHUMATED;
  $scope.STATUS_CHOICES = STATUS_CHOICES;
  $scope.PHONETYPE_CHOICES = PHONETYPE_CHOICES;
  $scope.grave_page = 1;
  $scope.log_page = 1;
  $scope.loading = false;
  $scope.edit_resp = false;
  $scope.editor = {
    isAddressEdited: false,
    isResponsibleEdited: false,
    isPhoneEdited: false
  };
  $scope.isLoginFormOpen = false;

  var item_params;
  //setup
  $scope.updateMap = function () {
    if ($scope.item) {
      ymapData.markers = [
        {
          point: [
            geo.getLat($scope.item.lat),
            geo.getLng($scope.item.lng)
          ],
          caption: 'Место: "{0}"'.format($scope.item.place),
          content: "Кл. {0}, уч. {1}, ряд {2}, место {3}".format(
            $scope.cemetery.name,
            $scope.area.name,
            $scope.item.row || '-',
            $scope.item.place),

          obj_type: 'place',
          id: $scope.item.id
        }
      ];
      $scope.placeCoordinates = [
        {
          point: [
            geo.getLat($scope.item.lat),
            geo.getLng($scope.item.lng)
          ],
          title: $scope.item.name,
          obj_type: 'place',
          id: $scope.item.id
        }
      ];
    } else {
      ymapData.markers = [];
    }

    ymapData.points = [];
    angular.forEach($scope.graves, function (grave, key) {
      if (grave.lat && grave.lng) {
        ymapData.points.push({
          point: [
            geo.getLat(grave.lat || $scope.item.lat),
            geo.getLng(grave.lng || $scope.item.lng)
          ],
          caption: 'Могила {0}'.format(grave.grave_number),
          content: '',
          obj_type: 'grave',
          id: grave.pk
        });
      }
    });
    $scope.$broadcast('handleMapChanged');
  };

  $scope.update = function () {
    $scope.loading = true;
    item_params = {
      placeID: $routeParams.place_id,
      cemetery_id: $routeParams.cemetery_id,
      area_id: $routeParams.area_id,
      grave_page: $scope.grave_page,
      log_page: $scope.log_page
    };
    $scope.address_class = 'Place';
    $scope.address_class_params = item_params;

    Place.getForm(item_params, function (result) {
      // Prepare place gallery
      if (result.place.gallery.length) {
        $scope.placeGallery = _(result.place.gallery)
          .sortBy('addedAt')
          .reverse()
          .value();
        $scope.placeGalleryFirstPhoto = $scope.placeGallery[0];
      }

      $scope.cemetery = new Cemetery(result.cemetery);
      $scope.area = new Area(result.area);
      $scope.item = new Place(result.place);
      $scope.item.place_length = parseFloat($scope.item.place_length); // html5 input[type=number]
      $scope.item.place_width = parseFloat($scope.item.place_width);

      $scope.editor.caretaker = result.place.caretaker;
      $scope.editor.caretakers = result.caretakers;
      $scope.caretaker_show = caretakerShow(
            result.place.caretaker,
            result.caretakers
      );

      $scope.place_log = [];
      angular.forEach(result.log, function (item) {
        $scope.place_log.push(new Log(item));
      });

      $scope.log_page = result.log_page;
      $scope.log_pages = result.log_pages;

      $scope.responsible_address = new Address(result.responsible_address);
      $scope.responsible_phones = [];
      angular.forEach(result.responsible_phones, function (item) {
        $scope.responsible_phones.push(new Phone(item));
      });

      //$scope.burials = new Burial(result.burials);
      //$scope.graves = new Grave(result.graves);

      if (result.responsible) {
        $scope.responsible = new AlivePerson(result.responsible);
      } else {
        $scope.responsible = new AlivePerson({
          is_new: true
        });
      }

      $scope.item.name = $scope.cemetery.name;
      $scope.loading = false;

      $scope.grave_count = result.grave_count;
      if ($scope.placeCoordinates) {
        var lat = $scope.placeCoordinates.lat, lng = $scope.placeCoordinates.lng;
      }
      $scope.newGrave = new Grave({
        place: $scope.item.id,
        is_wrong_fio: false,
        is_military: false,
        grave_number: $scope.grave_count + 1 //todo add way to count next grave_number or add validation of grave_number
        //lat :geo.getLat(lat || $scope.item.lat),
        //lng :geo.getLng(lng || $scope.item.lng )
      });
      $scope.updateGraves();
    }, function (data) {
      $scope.loading = false;
      if (data.status == 404) {
        window.location = '/manage/404?title=Место не найдено';
      }
    });

  };

  $scope.updateGraves = function () {
    $scope.loading = true;

    item_params.grave_page = $scope.grave_page;

    Place.getGraves(item_params, function (graves) {
      $scope.grave_page = graves.page || 1;
      $scope.grave_pages = graves.pages;
      delete $scope.graves;
      $scope.graves = [];
      angular.forEach(graves.graves, function (row, key) {
        var grave = new Grave(row);
        $scope.graves.push(grave);
      });
      delete $scope.burials;
      $scope.burials = [];
      var burial;
      angular.forEach(graves.burials, function (row, key) {
        burial = new Burial(row);
        $scope.burials.push(burial);
      });
      $scope.burials = _($scope.burials)
        .sortBy('fact_date')
        .reverse()
        .value();

      $scope.updateMap();
      $scope.loading = false;
      return;

      if ($scope.placeCoordinates) {
        var lat = $scope.placeCoordinates.lat, lng = $scope.placeCoordinates.lng;
      }
      // New element with default data
      $scope.newGrave = new Grave({
        is_wrong_fio: false,
        is_military: false,
        place: $scope.item.id,
        grave_number: $scope.graves.length + 1 //todo add way to count next grave_number or add validation of grave_number
        //lat :geo.getLat(lat || $scope.item.lat),
        //lng :geo.getLng(lng || $scope.item.lng )
      });
    }, function (data) {
      $scope.loading = false;
    });
    /*Burial.query({
     cemetery_id : $routeParams.cemetery_id,
     area_id : $routeParams.area_id,
     place_id : $routeParams.place_id
     }, function(result) {
     $scope.burials = result;
     });*/
  };


  $scope.$watch("log_page", $scope.update);
  $scope.$watch("grave_page", $scope.updateGraves);


  //alerts
  $scope.alerts = [];
  $scope.closeAlert = function (index) {
    $scope.alerts.splice(index, 1);
  };
  //$scope.alerts.push({msg: "Another alert!"});

  //todo extrude place and burial edit in separate controllers with tpl
  // Diallog
  $scope.opts = {
    backdropFade: true,
    dialogFade: true
  };

  $scope.cancelExhumation = function (burial) {
    var item_params = {
      placeID: $routeParams.place_id,
      cemetery_id: $routeParams.cemetery_id,
      area_id: $routeParams.area_id,
      burial_id: burial.id
    };
    Place.cancelExhumation(item_params, function (result) {
      $scope.updateGraves();
    });
  };

  $scope.openEditForm = function (form, data) {
    $scope[form] = true;
    $('body').css('overflow-y', 'hidden');
    $scope.editor.action = form;
    switch (form) {
      case 'isResponsibleEditorOpen':
        $scope.editor.item = angular.copy($scope.item);
        $scope.editor.responsible = angular.copy($scope.responsible);
        $scope.editor.responsible_phones = angular.copy($scope.responsible_phones);
        $scope.editor.responsible_address = angular.copy($scope.responsible_address);
        $scope.editor.isAddressEdited = false;
        $scope.editor.isResponsibleEdited = false;
        $scope.editor.isPhoneEdited = false;

        if (!$scope.editor.responsible_address.region)
          $scope.editor.responsible_address.region = {};
        if (!$scope.editor.responsible_address.country)
          $scope.editor.responsible_address.country = {};
        if (!$scope.editor.responsible_address.city)
          $scope.editor.responsible_address.city = {};
        if (!$scope.editor.responsible_address.street)
          $scope.editor.responsible_address.street = {};
        break;
      case 'isPlaceEditorOpen':
        $scope.editor.item = angular.copy($scope.item);
        break;
      case 'isBurialEditorOpen':
        if (data) {
          Burial.get({
            cemetery_id: $routeParams.cemetery_id,
            area_id: $routeParams.area_id,
            place_id: $routeParams.place_id,
            burialID: data.id
          }, function (result) {
            result.plan_time = result.plan_time || '';
            $scope.selectedBurial = result;
            $scope.editor.item = $scope.selectedBurial;
          });
        }
        break;
      case 'isGraveAddOpen':
        if ($scope.placeCoordinates) {
          var lat = $scope.placeCoordinates.lat, lng = $scope.placeCoordinates.lng;
        }
        $scope.newGrave = new Grave({
          is_wrong_fio: false,
          is_military: false,
          place: $scope.item.id,
          grave_number: $scope.grave_count + 1 //todo add way to count next grave_number or add validation of grave_number
          //lat :geo.getLat(lat || $scope.item.lat),
          //lng :geo.getLng(lng || $scope.item.lng )
        });
        break;
      case 'isGraveEditOpen':
        if (data) {
          $scope.selectedGrave = data;
          $scope.originGraveNumber = data.grave_number;
          $scope.editor.gave = data;
        }
        break;
      case 'isPlaceGalleryOpen':
        if (data) {
          $scope.selectedPlacePhotos = data;
          $scope.setCurrentImage(_.first(data));
        }
        break;
    }
  };

  $scope.setCurrentImage = function (image) {
    $scope.currentImage = image;
  };

  $scope.closeEditForm = function (form) {
    $scope[form] = false;
    $('body').css('overflow-y', 'auto');
  };

  //Place
  $scope.isPlaceEditorOpen = false;
  $scope.savePlaceEditForm = function (form) {
    if (form.$valid) {
      var url = '/manage/cemetery/{0}/area/{1}/place/{2}'.format($scope.item.cemetery, $scope.item.area, $scope.item.id);
      $scope.loading = true;
      $scope.editor.item.caretaker = $scope.editor.caretaker;
      $scope.editor.item.$update({
        cemetery_id: $routeParams.cemetery_id,
        area_id: $routeParams.area_id
      }, function () {
        $scope.update();
        $scope.updateMap();
        $scope.closeEditForm('isPlaceEditorOpen');
        noty({text: 'Изменения сохранены', type: 'success', layout: 'topRight'});
        $location.path(url);
        $location.replace();
        //$scope.update();
      });
    }
  };

  //Responsible
  $scope.isResponsibleEditorOpen = false;
  $scope.saveResponsibleEditForm = function (form) {
    if (form.$valid || true) { //TODO: check this
      $scope.editor.item.obj_responsible = $scope.editor.responsible;
      $scope.editor.item.obj_responsible_phones = $scope.editor.responsible_phones;
      $scope.editor.item.obj_responsible_address = $scope.editor.responsible_address;

      $scope.loading = true;
      $scope.editor.item.$update({
        cemetery_id: $routeParams.cemetery_id,
        area_id: $routeParams.area_id
      }, function (response) {
        noty({text: 'Изменения сохранены', type: 'success', layout: 'topRight'});
        $scope.closeEditForm('isResponsibleEditorOpen');
        $scope.update();
      });
    } else {
      var msg = "Исправьте ошибки в форме";
      noty({text: msg, type: 'error', layout: 'topRight'});
    }
  };
  $scope.responsible_edit = function () {
    // https://trello.com/c/eyBZRdiM/803--
    var o = $scope.editor.responsible;
    $scope.editor.isResponsibleEdited = true;
    $scope.editor.responsible_copy = {
      last_name: o.last_name,
      first_name: o.first_name,
      middle_name: o.middle_name,
      login_phone: o.login_phone
    }
  };
  $scope.responsible_edit_cancel = function () {
    // https://trello.com/c/eyBZRdiM/803--
    var o = $scope.editor.responsible_copy;
    $scope.editor.isResponsibleEdited = false;
    $scope.editor.responsible.last_name = o.last_name;
    $scope.editor.responsible.first_name = o.first_name;
    $scope.editor.responsible.middle_name = o.middle_name;
    $scope.editor.responsible.login_phone = o.login_phone;
  };

  $scope.removeResponsible = function () {
    if ($scope.responsible.last_name || $scope.responsible.first_name || $scope.responsible.middle_name) {
      var fio = "{0} {1} {2}".format($scope.responsible.last_name, $scope.responsible.first_name, $scope.responsible.middle_name);
      if (confirm("Открепить " + fio + '?')) {
        delete $scope.item.responsible;
        $scope.loading = true;
        $scope.item.$update({placeID: $routeParams.place_id,
          cemetery_id: $routeParams.cemetery_id,
          area_id: $routeParams.area_id
        }, function () {
          noty({text: fio + " откреплен.", type: 'success', layout: 'topRight'});
          $scope.update();
        });
      }
    }
  };

  $scope.onCemeteryChanged = function ($item, $model) {
    if ($item) {
      Area.query({
        cemetery_id: $item.id
      }, function (result) {
        $scope.area_list = result;
      });

      $scope.area = undefined;
      $scope.cemetery = $item;
    }
  };

  $scope.onAreaChanged = function ($item, $model, $value) {
    if ($item) {
      $scope.area = $item;
    }
  };

  //Grave

  $scope.graveMove = function (direction, grave) {
    $scope.loading = true;
    grave.$move({
      cemetery_id: $routeParams.cemetery_id,
      area_id: $routeParams.area_id,
      place_id: $routeParams.place_id,
      graveID: grave.id,
      direction: direction
    }, function (data) {
      $scope.update();
    });
  };

  $scope.isGraveAddOpen = false;

  $scope.addGrave = function (form) {
    if (form.$valid) {
      $scope.loading = true;
      $scope.newGrave.$save(function () {
        $scope.closeEditForm('isGraveAddOpen');
        $scope.updateGraves();
        var msg = "Могила добавлена.";
        noty({text: msg, type: 'success', layout: 'topRight'});
        $scope.update();
      });
    } else {
      var msg = "Исправьте ошибки в форме";
      noty({text: msg, type: 'error', layout: 'topRight'});
    }
  };

  $scope.isGraveEditOpen = false;
  $scope.saveGraveEditForm = function (form) {
    if (form.$valid) {
      $scope.loading = true;
      $scope.selectedGrave.$update({
        cemetery_id: $routeParams.cemetery_id,
        area_id: $routeParams.area_id,
        place_id: $routeParams.place_id
      }, function (targetGrave) {
        //graveUpdateHandler();
        //TODO: E.St.: is it necessary?
        /*if (targetGrave) {
         //targetGrave.$update(graveUpdateHandler);
         } else {
         graveUpdateHandler();
         }*/
        $scope.closeEditForm('isGraveEditOpen');
        var msg = "Изменения сохранены.";
        noty({text: msg, type: 'success', layout: 'topRight'});
        $scope.update();
      });
    } else {
      var msg = "Исправьте ошибки в форме";
      noty({text: msg, type: 'error', layout: 'topRight'});
    }
  };

  $scope.deleteGrave = function (grave) {

    var title = 'Подтверждение удаления',
      msg = 'Все прикрепленные фотографии также будут удалены',
      btns = [
        {result: 'ok', label: 'Удалить'},
        {result: 'cancel', label: 'Отмена', cssClass: 'btn-primary'}
      ];
    $scope.grave_to_delete = grave;
    $dialog.messageBox(title, msg, btns)
      .open()
      .then(function (result) {
        if (result == 'ok') {
          //var grave = new Grave($scope.grave_to_delete);
          $scope.grave_to_delete.$delete({
            cemetery_id: $routeParams.cemetery_id,
            area_id: $routeParams.area_id,
            place_id: $routeParams.place_id,
            graveID: grave.id
          }, function () {
            $scope.updateGraves();
            var msg = "Могила удалена.";
            noty({text: msg, type: 'success', layout: 'topRight'});
            delete $scope.grave_to_delete;
            $scope.update();
          });
        }
      });
  };

  $scope.haveBurials = function (graveID) {
    return _.any($scope.burials, function (burial) {
      return burial.grave === graveID;
    });
  };

  $scope.isPlaceGalleryOpen = false;

  //Burial
  $scope.isBurialEditorOpen = false;
  $scope.saveBurialEditForm = function (form) {
    if (form.graveNumber.$dirty && form.$valid) {
      $scope.selectedBurial.grave = $scope.selectedBurial.grave.id;
      $scope.selectedBurial.$update({
        cemetery_id: $routeParams.cemetery_id,
        area_id: $routeParams.area_id,
        place_id: $routeParams.place_id
      }, function () {
        $scope.closeEditForm('isBurialEditorOpen');
        $scope.updateGraves();
        var msg = "Изменения сохранены.";
        noty({text: msg, type: 'success', layout: 'topRight'});
      });
    }
  };
  // EOF Diallog

  // RUN
  $scope.$on("$routeChangeSuccess", function (event) {
    $scope.update();
  });

  $scope.$on("mapPointChanged:place", function (event, data) {
    if ($scope.item.id == data.obj_id) {
      $scope.item.lat = data.coords[0];
      $scope.item.lng = data.coords[1];
      $scope.$digest();
      $scope.item.$update({
        cemetery_id: $routeParams.cemetery_id,
        area_id: $routeParams.area_id
      }, function (data) {
        $scope.update();
      });
    }
  });
  $scope.is_responsible_disabled = function (responsibleEditForm, responsibleEditFormAddr) {
    var o = $scope.editor;
    var form1_valid = responsibleEditForm.$valid,
      form2_valid = o.isAddressValid || (responsibleEditFormAddr && responsibleEditFormAddr.$valid),
      form3_valid = !o.isPhoneEdited &&
        (
          (o.responsible_phones && o.responsible_phones.length > 0) ||
            (o.responsible.login_phone && o.responsible.login_phone.length > 0)
          );

    return !(
      !(o.isResponsibleEdited || o.isAddressEdited || o.isPhoneEdited) &&
        form1_valid && (form2_valid || form3_valid)
      );
  };

  $scope.validatePhone = function (value) {
    return !(value && value.length) || (value && value.replace('-', '').match(/^[1-9][\d]{9,11}$/) != null)
  };

  ymapData.markers = [];
  ymapData.points = [];
  $scope.$broadcast('handleMapChanged');

});
