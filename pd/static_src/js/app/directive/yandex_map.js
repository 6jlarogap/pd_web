app.directive('yandexMap', function($q){

	var mapPromise, ymap;

	//set up a promise which will show map when Yandex API will be loaded
	function loadMap(mapData){
		/*
		 // SK: singleton temporarry turned off
		 UPD: need full canvas redraw
		 $scope.savePlaceEditForm - $scope.updatePlace();  (need check $location.replace)
		 */	
		if (mapPromise) {
			return mapPromise;
		}

		var deferred = $q.defer();
		mapPromise = deferred.promise;

		ymaps.ready(function(){
			ymap = new ymaps.Map("yandex-map", {
				center:[ymaps.geolocation.latitude, ymaps.geolocation.longitude],
				zoom: 16
			});
			ymap.controls.add('zoomControl');
			ymap.controls.add('mapTools');
			ymap.controls.add('typeSelector');
			deferred.resolve(mapData);
		});
		return mapPromise;
	}

	return {
		restrict: 'EA',
		replace: true,
		template: '<div id="yandex-map"></div>',
		link: function(scope, element, attrs){
			loadMap(attrs).then(function(mapData) {
				var mapObj, data;


				try{
					eval('data='+mapData.data);
					if(!data.length)
						throw Error('Empty coordinates array');
				}catch(e){
					return;
				}
				
				//console.log("data", mapData.data, data);
				//console.log([data[0].lat , data[0].lng]);
				//ymap.setCenter([data[0].lat , data[0].lng], 16);

				
				/*if(!data.length) 
					return;*/
				/*var ymap = new ymaps.Map("yandex-map", {
					center: [data[0].lat , data[0].lng],
					zoom: 16
				});*/
				
				for(var i=0;i< data.length;i++){
					var obj = data[i];
					if(obj.ico==1){
						mapObj = new ymaps.Placemark([obj.lat, obj.lng], {
					            balloonContentHeader: obj.title,
					            balloonContent: mapData.markerBody
					        }
					    );
					}else{ // if(obj.ico==2)
						mapObj = new ymaps.Circle([[obj.lat, obj.lng], 5], {
							hintContent: obj.title,
							balloonContent: obj.title
						}, {
						    geodesic: true
						});						
					}
					ymap.geoObjects.add(mapObj);
				}
				//ymap.container.fitToViewport();
	        });
		}
	};
});