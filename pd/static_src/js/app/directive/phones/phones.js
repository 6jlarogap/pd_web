app.controller('PhonesController', ['$scope', 'Phone', function($scope, Phone) {
	var self = this;

    var DEFAULT_PHONETYPE = PHONE_TYPE_MOBILE;
	$scope.PHONETYPE_CHOICES = PHONETYPE_CHOICES;
    $scope.isPhoneEditorOpen = false;
    $scope.isPhoneAddOpen = false;
    $scope.isStaticBlock = false;
    $scope.requireTel = true;
    $scope.maxlength = 12;
    
    $scope.phone = new Phone({is_new:true, phonetype:DEFAULT_PHONETYPE});
    
    $scope.phoneNumberPattern = (function() {
        var regexp = /^\(?(\d{3})\)?[ .-]?(\d{3})[ .-]?(\d{4})$/;
        return {
            test: function(value) {
                if( $scope.requireTel === false ) return true;
                else return regexp.test(value);
            }
        };
    })();
        
    $scope.update = function(obj) {
        /*if (!$scope.phones){
	        Phone.query(function(result){
				$scope.phones = result;
			});
        }else{
            
        }*/
	};
    $scope.$watch('phones', function() {
		$scope.update();
	});
        
	$scope.open = function(data){
		if(data){
            $scope.phone=data;
			$scope.isPhoneEditOpen = true;
            $scope.isStaticBlock = true;
        }else{
            $scope.phone = new Phone({is_new:true, phonetype:DEFAULT_PHONETYPE});
            $scope.isPhoneAddOpen = true;
            $scope.isStaticBlock = true;
        }
	};
	$scope.close = function() {
    //    $scope.phones = undefined;
		$scope.update();
		$scope.isPhoneEditOpen = false;
        $scope.isPhoneAddOpen = false;
        $scope.isStaticBlock = false;
	};
        
    $scope.destroy = function(index){
        //delete phone
        $scope.phones.splice(index, 1);
    };
        
    $scope.save = function() {
		if($scope.phone.is_new){
			$scope.phone.is_new = false;
			$scope.phones.push($scope.phone);
            $scope.isPhoneEditOpen = false;
            $scope.isPhoneAddOpen = false;
            $scope.isStaticBlock = false;
			/*obj.$save(function(resource) {
				//save phone
			});*/
		}else{
			/*obj.$update(function(resource) {
				//update phone
			});*/
            $scope.isPhoneEditOpen = false;
            $scope.isPhoneAddOpen = false;
            $scope.isStaticBlock = false;
        }
	};
	
	$scope.validatePhone = function(value) {
	    return value && value.match(/^((8|\+7|\+375)[\- ]?)?(\(?\d{2,3}\)?[\- ]?)?[\d\- ]{7,10}$/) != null 
	};
	
	
	if(!($scope.phones && $scope.phones.length)){
		$scope.open();
	}
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
