
app.filter('list', function() {
    return function(value,list) {
        return list?list[value]: value;
    };
});


app.filter('objList', function() {
    return function(value,list) {
    	if(list && list.length)
			for(var i=0;i<list.length;i++)
				if(list[i].id == value)
					return list[i].name;
	};
});


app.directive('bsTypeahead', [
  '$parse',
  function ($parse) {
    return {
     // restrict: 'A',
      require: '?ngModel',
      link: function postLink(scope, element, attrs, controller) {
        var getter = $parse(attrs.bsTypeahead), setter = getter.assign, value = getter(scope);
        scope.$watch(attrs.bsTypeahead, function (newValue, oldValue) {
          if (newValue !== oldValue) {
            value = newValue;
          }
        });
        element.attr('data-provide', 'typeahead');
        element.typeahead({
          source: function (query) {
            return angular.isFunction(value) ? value.apply(null, arguments) : value;
          },
          minLength: attrs.minLength || 1,
          items: attrs.items,
          updater: function (value) {
            if (controller) {
              scope.$apply(function () {
                controller.$setViewValue(value);
              });
            }
            scope.$emit('typeahead-updated', value);
            return value;
          }
        });
        var typeahead = element.data('typeahead');
        typeahead.lookup = function (ev) {
          var items;
          this.query = this.$element.val() || '';
          if (this.query.length < this.options.minLength) {
            return this.shown ? this.hide() : this;
          }
          items = $.isFunction(this.source) ? this.source(this.query, $.proxy(this.process, this)) : this.source;
          return items ? this.process(items) : this;
        };
        if (!!attrs.matchAll) {
          typeahead.matcher = function (item) {
            return true;
          };
        }
        if (attrs.minLength === '0') {
          setTimeout(function () {
            element.on('focus', function () {
              element.val().length === 0 && setTimeout(element.typeahead.bind(element, 'lookup'), 200);
            });
          });
        }
      }
    };
  }
]);


function get_thumbnail_url(url, width, height, method){
	/*
	 get_thumbnail_url('logo.jpg',200,200,'crop')
	 >> "/thumb/logo.jpg/200x200~crop~12.jpg"
	 width : pixels
	 height: pixels
	 method: [crop, scale, smart]
	 */
	if(!url) return '';

  // Split image full url by "/media/" predicate
  var urlChunks = url.split('/media/');
  if (2 == urlChunks.length) {
    url = urlChunks[1];
  }

	return '/thumb/{0}/{1}x{2}~{3}~12.jpg'.format(url, width.toString(), height.toString(), method)
}


app.filter('thumbnail', function() {
	/*
	 Angularjs: create thumbnail from url
	 {{ item.url | thumbnail:200:200:'crop' }}
	 width : pixels
	 height: pixels
	 method: [crop, scale, smart]
	 */
    return function(value, width, height, method) {
    	return get_thumbnail_url(value, width, height, method)
	};
});

/*app.filter('thumbnail_img', function() {
    return function(value, width, height, method, class_value) {
    	var url= get_thumbnail_url(value, width, height, method)
    	return '<img src="{0}" width="{1}px" height="{2}px" class="{3}"/>'.format(
    			url, width.toString(), height.toString(), class_value)
	};
});
*/

app.filter('momentDate', function () {
  return function (value, format) {
    var momentDate = moment(value);
    if (!momentDate.isValid()) {
      return null;
    }

    return momentDate.format(format);
  };
});
