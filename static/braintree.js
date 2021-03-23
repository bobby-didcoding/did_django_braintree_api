

$.getScript( "https://js.braintreegateway.com/web/dropin/1.24.0/js/dropin.min.js", function() {
 
  var button = document.querySelector('#btBtnbutton');

  braintree.dropin.create({
    authorization: braintree_client_token,
    container: '#bt-dropin',
    card: {
      cardholderName: {
        required: false
      }
    },
    paypal: {
      flow: 'vault'
    },
    venmo: {
      allowNewBrowserTab: false
    }
  }, function (createErr, instance) {
    button.addEventListener('click', function (event) {
      event.preventDefault();
      instance.requestPaymentMethod(function (err, payload) {
        CustomFormSubmitPost($('#btBtnbutton'));
        $.ajax({
          type: 'POST',
          url: "/payment",
          data: {
            paymentMethodNonce: payload.nonce,
            amount: "16.52",
            currency: "gbp",
            description: "Shirt",
          },
          success: function(json){

            if (json["result"] == "okay") {
              alert("Your payment was a success");
              window.location.assign("/account")
            }
            else{
              CustomFormSubmitResponse($('#btBtnbutton'));
              alert(json["message"]);

            }
          },
          error: function(xhr){
            CustomFormSubmitResponse($('#btBtnbutton'));
            console.log(xhr.status + ": " + xhr.responseText);
          }
        }).done(function (result) {
         //do accordingly
        });
      


      });
    });
  });
})