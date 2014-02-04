app.controller('PhonesController', ['$scope', 'Phone', function($scope, Phone) {
	var self = this;

    var DEFAULT_PHONETYPE = PHONE_TYPE_MOBILE;
	$scope.PHONETYPE_CHOICES = PHONETYPE_CHOICES;
    $scope.isPhoneEditorOpen = false;
    $scope.isPhoneAddOpen = false;
    $scope.isStaticBlock = false;
    $scope.requireTel = true;
    $scope.maxlength = 12;
    $scope.old = {};
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
		if(!$scope.phones){
			$scope.phones = [];
		}
		$('#edit_save_btn').data('disabled',$('#edit_save_btn').attr('disabled'));
		$('#edit_save_btn').attr('disabled','disabled');
		$scope.old = angular.copy($scope.phone);
	};
	$scope.close = function(form) {
		$scope.phone.phonetype = $scope.old.phonetype; 
		$scope.phone.number = $scope.old.number;
		//$scope.update();
		$scope.isPhoneEditOpen = false;
        $scope.isPhoneAddOpen = false;
        $scope.isStaticBlock = false;
        //$('#edit_save_btn').removeAttr('disabled');
        if( $('#edit_save_btn').data('disabled')){
        	$('#edit_save_btn').removeAttr('disabled');
        }
	};
        
    $scope.destroy = function(index){
        //delete phone
        $scope.phones.splice(index, 1);
    };
        
    $scope.save = function() {
		if($scope.phone.is_new && $scope.phone.number.length){
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
		//$('#edit_save_btn').removeAttr('disabled');
        if( $('#edit_save_btn').data('disabled')){
        	$('#edit_save_btn').removeAttr('disabled');
        }
	};
	
	$scope.validatePhone = function(value) {
	    //return value && value.length>0 && value.match(/^(\d{1,5}?)(\(?\d{2,3}\)?[\- ]?)[\d\- ]{7,12}$/) != null 
	    //return value && value.length>0 && value.match(/^(\d{1,5}?)?(\(?\d{2,3}\)?[\- ]?)?[\d\- ]{5,12}$/) != null
	    return value && value.replace('-','').match(/^[\d]{10,12}$/) != null
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
