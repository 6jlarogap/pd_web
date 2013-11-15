app.controller('PhonesController', ['$scope', '$dialog', '$http', '$resource', 'Phone',
function($scope, $dialog, $http, $resource, $parse, Phone) {
	var self = this;

	$scope.PHONE_TYPE_CHOICES = PHONE_TYPE_CHOICES;
                 
        $scope.isPhoneEditorOpen = false;
        $scope.isPhoneAddOpen = false;
        $scope.isStaticBlock = false;
        //deal with directive(not visible)
        var Phone=$resource('/static/js/app/phones.json');
        
        $scope.update = function() {
        if (!$scope.phones)
        {
        Phone.query(function(result) {
			$scope.phones = result;
		});
            }
            else
            {
                
            }
	};
        $scope.$watch('phones', function() {
		$scope.update();
	});
        
	$scope.open = function(data) {
                if (data) {
                $scope.phone=data;
		$scope.isPhoneEditOpen = true;
                $scope.isStaticBlock = true;
                }
                else
                {
                    $scope.phone = new Phone();
                    $scope.phone.is_new = true;
                    $scope.isPhoneAddOpen = true;
                    $scope.isStaticBlock = true;
                }
	};
	$scope.close = function() {
                $scope.phones = undefined;
		$scope.update();
		$scope.isPhoneEditOpen = false;
                $scope.isPhoneAddOpen = false;
                $scope.isStaticBlock = false;
	};
        
        $scope.destroy = function()
        {
            //delete phone
        };
        
        $scope.save = function() {
		if ($scope.phone.is_new) {
			$scope.phones.push($scope.phone);
                        $scope.isPhoneEditOpen = false;
                        $scope.isPhoneAddOpen = false;
                        $scope.isStaticBlock = false;
//			$scope.phone.$save(function(obj) {
//				//save phone
//			});
		} else {
//			$scope.item.$update(function(obj) {
//				//update phone
//			});
                        $scope.isPhoneEditOpen = false;
                        $scope.isPhoneAddOpen = false;
                        $scope.isStaticBlock = false;
		}
	};

}]);


app.directive('phones', [
function() {
	return {
		restrict : 'EA',
		controller : 'PhonesController',
		require : 'phones',
		templateUrl : STATIC_APP_URL + '/directive/phones/phones.html' + version_str,
		scope : {
			phones : '=',
			save_action : '&'
		}

	};
}]);




