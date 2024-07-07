// dropupload.js
// Copyright 2020 Kord Campbell. All rights reserved.

/* drop upload or click*/
var upfunk = function(button_id, image_preview_id, title, tags, upload_url, callback) {
  var dropRegion = document.getElementById(button_id);
  var imagePreviewRegion = document.getElementById(image_preview_id);

  // open file selector when clicked
  var fakeInput = document.createElement("input");
  fakeInput.type = "file";
  fakeInput.accept = "image/*,.pdf,.txt";
  fakeInput.multiple = true;
  dropRegion.addEventListener('click', function() {
    fakeInput.click();
  });

  fakeInput.addEventListener("change", function() {
    var files = fakeInput.files;
    handleFiles(files, upload_url);
  });

  function preventDefault(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  dropRegion.addEventListener('dragenter', preventDefault, false)
  dropRegion.addEventListener('dragleave', preventDefault, false)
  dropRegion.addEventListener('dragover', preventDefault, false)
  dropRegion.addEventListener('drop', preventDefault, false)

  function handleDrop(e) {
    var dt = e.dataTransfer;
    var files = dt.files;

    handleFiles(files, upload_url);
  }

  dropRegion.addEventListener('drop', handleDrop, false);

  function handleFiles(files, upload_url) {
    for (var i = 0, len = files.length; i < len; i++) {
      if (validateImage(files[i])) {
        previewAnduploadImage(files[i], upload_url);
      }
    }
  }

  function validateImage(image) {
      // check the type
      var validTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain'];
      if (validTypes.indexOf( image.type ) === -1) {
          alert("Invalid File Type");
          return false;
      }

      // check the size
      var maxSizeInBytes = 100e6; // 100MB
      if (image.size > maxSizeInBytes) {
          alert("File too large");
          return false;
      }

      return true;
  }

  // ID maker 
  function MakeID(length) {
    var result = '';
    var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for ( var i = 0; i < length; i++ ) {
      result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
  }

  // thumb sizes
  function Thumb(doc_width, doc_height) {
    // compute sizes for images
    var height = 320;
    var width = 320;
    
    if(doc_width > doc_height) {
      console.log("landscape");
      var width_ratio = doc_width/320;
      height = doc_height/width_ratio;
    } else {
      console.log("portrait")
      var height_ratio = doc_height/320;
      width = doc_width/height_ratio;
    }
    return {'width': width, 'height': height};
  }

  // hasher
  function hashCode(filename) {
    var hash = 0, i, chr;
    if (filename.length === 0) return hash;
    for (i = 0; i < filename.length; i++) {
      chr   = filename.charCodeAt(i);
      hash  = ((hash << 5) - hash) + chr;
      hash |= 0; // Convert to 32bit integer
    }
    return Math.abs(hash);
  };

  function previewAnduploadImage(image, upload_url) {
      // container
      var imgView = document.createElement("div");
      imgView.className = "image-view";
      imagePreviewRegion.appendChild(imgView);

      if (image.type == "application/pdf") {
        var canvas = document.createElement("canvas");
        var canvasID = MakeID(7);
        canvas.setAttribute('id', 'the-canvas-'+canvasID);
        imgView.appendChild(canvas);

        // progress overlay
        var overlay = document.createElement("div");
        overlay.className = "overlay";
        imgView.appendChild(overlay);
      } else {
        // previewing image
        var img = document.createElement("img");

        // hide the image until it loads and we know the size
        img.style.visibility = "hidden";
        imgView.appendChild(img);

        // progress overlay
        var overlay = document.createElement("div");
        overlay.className = "overlay";
        imgView.appendChild(overlay);  
      }
      
      // scroll
      var scroller = setTimeout(function() {
        var elmnt = document.getElementById(image_preview_id);
        elmnt.scrollIntoView();
      },200);
      
      // read the image...
      var reader = new FileReader();
      reader.onload = function(e) {
        if (image.type == "application/pdf") {
          var pdfjsLib = window['pdfjs-dist/build/pdf'];

          // TODO load this locally
          pdfjsLib.GlobalWorkerOptions.workerSrc = '//mozilla.github.io/pdf.js/build/pdf.worker.js';
          var loadingTask = pdfjsLib.getDocument(e.target.result);

          loadingTask.promise.then(function(pdf) {
            // Fetch the first page
            var pageNumber = 1;
            pdf.getPage(pageNumber).then(function(page) {
              // Prepare canvas using PDF page dimensions
              var canvas = document.getElementById('the-canvas-'+canvasID);
              var context = canvas.getContext('2d');
              var viewport = page.getViewport({scale: 1.0});
              
              viewport = page.getViewport({scale: 240 / viewport.width});
              canvas.height = viewport.height;
              canvas.width = viewport.width;

              // Render PDF page into canvas context
              var renderContext = {
                canvasContext: context,
                viewport: viewport
              };
              var renderTask = page.render(renderContext);
              renderTask.promise.then(function () {
                console.log('Page rendered');
              });
            });
          }, function (reason) {
            console.error(reason);
          });
        } else if (image.type = "text/plain") {
          // do nothing
        } else {
          // probably just an image
          img.setAttribute('id', "image-" + hashCode(image.name));

          img.src = e.target.result;
        }
      }

      // read the PDF image
      reader.readAsDataURL(image);

      if (img) {
        img.onload = function() {
          var height_width = Thumb(this.width, this.height);
          img.height = height_width.height;
          img.width = height_width.width;
          img.style.visibility = "visible";
        };
      }
      
      // create FormData
      var formData = new FormData();
      formData.append('images', image);
      formData.append('tags', tags);
      if (title) {
        formData.append('title', title);
      }

      // make request
      var ajax = new XMLHttpRequest();
      ajax.responseType = 'json';
      ajax.open("POST", upload_url, true);

      ajax.upload.onprogress = function(e) {
        var perc = (e.loaded / e.total * 100) || 100,
            width = 100 - perc;

        overlay.style.width = width;
      }

      ajax.onreadystatechange = function() {
          if (ajax.readyState == XMLHttpRequest.DONE) {
            console.log(ajax.response);
            callback(ajax.response.document_id, ajax.response.filename);
          }
      }

      ajax.send(formData);
  }

  return;
}
