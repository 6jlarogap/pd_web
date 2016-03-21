var map, ymaps;
var YMAPS_URL = '//api-maps.yandex.ru/2.0/?load=package.standard,package.clusters,package.geoObjects&mode=release&lang=ru-RU&ns=ymaps',

  ymapModule = angular.module('ymaps', [])
    .factory('$script', ['$q', '$rootScope', function ($q, $rootScope) {
      "use strict";
      //классический кроссбраузерный способ подключить внешний скрипт
      function loadScript(path, callback) {
        var el = document.createElement("script");
        el.onload = el.onreadystatechange = function () {
          if (el.readyState && el.readyState !== "complete" &&
            el.readyState !== "loaded") {
            return false;
          }
          // если все загрузилось, то снимаем обработчик и выбрасываем callback
          el.onload = el.onreadystatechange = null;
          if (angular.isFunction(callback)) {
            callback();
          }
        };
        el.async = true;
        el.src = path;
        document.getElementsByTagName('body')[0].appendChild(el);
      }

      var loadHistory = [], //кэш загруженных файлов
        pendingPromises = {}; //обещания на текущие загруки
      return {
        get: function (url) {
          var deferred = $q.defer();
          if (loadHistory.indexOf(url) !== -1) {
            deferred.resolve();
          }
          else if (pendingPromises[url]) {
            return pendingPromises[url];
          } else {
            loadScript(url, function () {
              delete pendingPromises[url];
              loadHistory.push(url);
              //обязательно использовать `$apply`, чтобы сообщить
              //angular о том, что что-то произошло
              $rootScope.$apply(function () {
                deferred.resolve();
              });
            });
            pendingPromises[url] = deferred.promise;
          }
          return deferred.promise;
        }
      };
    }])

    .constant('ymapConfig', {
      mapBehaviors: ['default', 'scrollZoom'],
      markerOptions: {
        preset: 'twirl#blueStretchyIcon',
        draggable: true
      },
      fitMarkers: false
    })

    .factory('ymapData', ['$rootScope', function ($rootScope) {
      var data = {
        map: false,
        markers: [],
        points: [],
        collection: []
      };
      return data;
    }])

    .controller('YmapController', ['$scope', '$rootScope', 'ymapData', function ($scope, $rootScope, ymapData) {
      //"use strict";
      $scope.bindActions = function (placeMark) {
        placeMark.events.add(['dragend'], function (e) {
          var pm = e.get('target');
          var data = {
            obj_type: pm.properties.get('obj_type'),
            obj_id: pm.properties.get('obj_id'),
            coords: pm.geometry.getCoordinates()
          };
          $rootScope.$broadcast('mapPointChanged:' + data.obj_type, data);
        });
      }

      $scope.addMarker = function (coordinates, properties, draggable, i) {
        var draggable_ = draggable === undefined ? true : draggable;
        var placeMark = new ymaps.Placemark(coordinates, properties, {draggable: draggable_, geodesic: true});
        //ymapData.markers[i].marker =  placeMark;
        ymapData.collection.add(placeMark);
        $scope.bindActions(placeMark);
        ymapData.map.setCenter(coordinates);
        return placeMark;
      };

      $scope.addCircle = function (coordinates, properties, i) {
        var placeMark = new ymaps.Circle([coordinates, 5], properties, {geodesic: true});
        ymapData.collection.add(placeMark);
        $scope.bindActions(placeMark);
        return placeMark;
      };
      $scope.removeMarkers = function () {
        /*ymaps.geoObjects.each(function (geoObject) {
         geoObject.remove();
         })*/
        ;
        if (ymapData.collection && ymapData.collection.removeAll)
          ymapData.collection.removeAll();
      };

      $scope.$on('handleMapChanged', function () {
        $scope.removeMarkers();
        if (ymapData.map) {
          draw_map_items($scope, ymapData);
        }
        // add defered resolving?
      });
    }])


    .directive('yandexMap', ['$compile', '$script', 'ymapConfig', 'ymapData', function ($compile, $script, config, ymapData) {
      "use strict";
      function initAutoFit(map, collection) {
        //brought from underscore http://underscorejs.org/#debounce
        function debounce(func, wait) {
          var timeout = null;
          return function () {
            var context = this, args = arguments;
            var later = function () {
              timeout = null;
              func.apply(context, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
          };
        }

        var fitMarkers = debounce(function (event) {
          var markerMargin = 0.1;
          var bounds = event.get('newBounds'),
          //make some margins from
            topRight = [
              bounds[1][0] + markerMargin,
              bounds[1][1] + markerMargin
            ],
            bottomLeft = [
              bounds[0][0] - markerMargin,
              bounds[0][1] - markerMargin
            ];
          map.setBounds([bottomLeft, topRight], {checkZoomRange: true});
        }, 300);
        collection.events.add('boundschange', fitMarkers);
      }

      return {
        restrict: 'EA',
        scope: {
          center: '=',
          zoom: '=',
          controls: '=',  // Sample data: ['mapTools', 'typeSelector',['zoomControl', { right: 5, top: 10 }]];
          coordinates: '=',
          points: '=',
          markers: '='
        },
        compile: function (tElement) {
          var childNodes = tElement.contents();
          tElement.html('');
          return function ($scope, element) {
            $script.get(YMAPS_URL).then(function () {
              ymaps.ready(function () {
                var map = new ymaps.Map(element[0], {
                  center: $scope.center || [ymaps.geolocation.latitude, ymaps.geolocation.longitude],
                  zoom: $scope.zoom || 12,
                  behaviors: config.mapBehaviors
                });


                var obj,
                  control_list = ['mapTools', 'typeSelector', 'zoomControl'];
                for (var i = 0; i < control_list.length; i++) {
                  obj = control_list[i];
                  if (typeof(obj) == 'string') {
                    map.controls.add(obj);
                  } else {
                    map.controls.add(obj[0], obj[1]);
                  }
                }

                //$scope.markers = new ymaps.GeoObjectCollection({}, config.markerOptions);
                ymapData.collection = new ymaps.GeoObjectCollection({}, config.markerOptions);
                //ymapData.collection = new ymaps.Clusterer({clusterDisableClickZoom: true},
                // 	config.markerOptions); //config.markerOptions);
                map.geoObjects.add(ymapData.collection);
                if (config.fitMarkers) {
                  initAutoFit(map, ymapData.collection);
                }
                $scope.map = map;
                ymapData.map = map;
                //$compile(childNodes)($scope.$parent);
                draw_map_items($scope, ymapData);

                $scope.$watch('markers', function (markers) {
                  _.forEach(markers, function (markerCoords) {
                    $scope.addMarker(markerCoords);
                  });
                });
              });
            });
          };
        },
        controller: 'YmapController'
      };
    }])
    .service('pdYandex', function ($q, $script, $rootScope) {
      return {
        geocode: function (address) {
          return $script.get(YMAPS_URL).then(function () {
            var deferred = $q.defer();

            ymaps.ready(function () {
              ymaps.geocode(address, { results: 1 }).then(function (res) {
                var firstGeoObject = res.geoObjects.get(0);
                if (!firstGeoObject) {
                  deferred.reject();
                  return;
                }

                deferred.resolve(firstGeoObject.geometry.getCoordinates());
                $rootScope.$digest();
              }, function (err) {
                deferred.reject(err);
              });
            });

            return deferred.promise;
          });
        }
      };
    })
  ;

function draw_map_items($scope, data) {
  $scope.removeMarkers();
  var marker, point, props, i;
  if (data.markers)
    for (i = 0; i < data.markers.length; i++) {
      point = data.markers[i].point;
      props = angular.extend({
        //iconContent: $scope.coordinates[i].icon,
        clusterCaption: data.markers[i].caption,
        balloonContentBody: data.markers[i].content
      }, $scope.properties);
      var draggable = data.markers[i].draggable === undefined ? true : data.markers[i].draggable;
      marker = $scope.addMarker(point, props, draggable, i);
      marker.properties.set('obj_id', data.markers[i].id);
      marker.properties.set('obj_type', data.markers[i].obj_type);
    }

  if (data.points)
    for (i = 0; i < data.points.length; i++) {
      point = data.points[i].point;
      props = angular.extend({
        clusterCaption: data.points[i].caption,
        balloonContentBody: data.points[i].content
      }, $scope.properties);
      marker = $scope.addCircle(point, props, i);
      marker.properties.set('obj_id', data.points[i].id);
      marker.properties.set('obj_type', data.points[i].obj_type);
    }
}

