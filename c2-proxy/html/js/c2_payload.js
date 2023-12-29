// payload window 

  $(function () {
    $("#submitBtn").off().on('click', function () {
      const hostname = $('#hostname').val();
      const port = $('#port').val();
      const url = '/api/payload/generate/' + hostname + '/' + port;
      $.ajax({
        url: url,
        type: 'GET',
        success: function (data) {
          // loop through the list and update span elements with IDs payload_text_0, payload_text_1, ...
          data = JSON.parse(data);
          data.forEach((value, index) => {
            const spanElement = $(`#payload_text_${index}`);
            if (spanElement.length > 0) {
              spanElement.text(value);
            }
          });
        },
        cache: false,
        contentType: false,
        processData: false
      });
    });
  
    $(document).on('click', '#copy_img', function () {
      const targetId = $(this).data('target');
      const payloadText = $(`#${targetId}`);
      const textToCopy = payloadText.text().trim();
      copyToClipboard(textToCopy);
    });
  
    function copyToClipboard(text) {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      // display copy contents in the modal view 
      $("#createModal .modal-body").text('Text copied to clipboard: ' + text);
      $("#createModal").modal("show");
      $("#create_ok").off().on('click', function () {
            $("#createModal").modal("hide");
      });
    }
  });
  