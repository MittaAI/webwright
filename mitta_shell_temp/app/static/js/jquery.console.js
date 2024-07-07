// JQuery Console 1.0
// Sun Feb 21 20:28:47 GMT 2010
//
// Copyright 2010 Chris Done, Simon David Pratt. All rights reserved.
//
// Copyright 2020-2022 Kord Campbell. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
//
//    1. Redistributions of source code must retain the above
//       copyright notice, this list of conditions and the following
//       disclaimer.
//
//    2. Redistributions in binary form must reproduce the above
//       copyright notice, this list of conditions and the following
//       disclaimer in the documentation and/or other materials
//       provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
// FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
// COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
// BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
// LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
// ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

// TESTED ON
//   Chrome
//   Firefox

(function($) {

  var isWebkit = !!~navigator.userAgent.indexOf(' AppleWebKit/');

  $.fn.console = function(config) {
    var keyCodes = {
      37: moveBackward,
      39: moveForward,
      38: previousHistory,
      40: nextHistory,
      8: backDelete,
      46: forwardDelete,
      35: moveToEnd,
      36: moveToStart,
      //13: commandTrigger,
      13: handleCommand,
      9: doComplete
    };
    var ctrlCodes = {
      65: moveToStart,
      69: moveToEnd,
      68: forwardDelete,
      78: nextHistory,
      80: previousHistory,
      66: moveBackward,
      70: moveForward,
      75: deleteUntilEnd,
      76: clearScreen,
      85: clearCurrentPrompt
    };
    if (config.ctrlCodes) {
      $.extend(ctrlCodes, config.ctrlCodes);
    }
    var altCodes = {
      70: moveToNextWord,
      66: moveToPreviousWord,
      68: deleteNextWord
    };

    var shiftCodes = {
      13: newLine,
    };

    var cursor = '<span class="jquery-console-cursor">&nbsp;</span>';

    // Globals
    var container = $(this);
    var inner = $('<div class="jquery-console-inner"></div>');
    var typer = $('<textarea id="box" style="opacity: 0.0001; width: 20px; height: 40px;" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" class="jquery-console-typer"></textarea>');

    // Prompt
    var promptBox;
    var prompt;
    var continuedPromptLabel = config && config.continuedPromptLabel ? config.continuedPromptLabel : "> ";
    var column = 0;
    var promptText = '';
    var restoreText = '';
    var continuedText = '';
    var fadeOnReset = config.fadeOnReset !== undefined ? config.fadeOnReset : false;

    var history = [];
    var ringn = 0;
    var cancelKeyPress = 0;
    var acceptInput = true;
    var cancelCommand = false;

    // External exports object
    var extern = {};

    // START HERE
    (function() {
      extern.promptLabel = config && config.promptLabel ? config.promptLabel : "> ";
      container.append(inner);

      // this is really awful
      inner.append(typer);
      typer.css({
        position: 'absolute',
      });

      if (config.welcomeMessage)
        message(config.welcomeMessage, 'jquery-console-welcome');

      newPromptBox();

      if (config.autofocus) {
        inner.addClass('jquery-console-focus');
        typer.focus();
        setTimeout(function() {
          inner.addClass('jquery-console-focus');
          typer.focus();
        }, 100);
      }

      extern.inner = inner;
      extern.typer = typer;
      extern.report = report;
      extern.addToHistory = addToHistory;
      extern.clearHistory = clearHistory;
      extern.getHistory = getHistory;
      extern.rotateHistory = rotateHistory;
      extern.getLastCommand = getLastCommand;
      extern.message = message;
      extern.clearScreen = clearScreen;
    })();

    ////////////////////////////////////////////////////////////////////////
    // Reset terminal
    extern.reset = function() {
      var welcome = (typeof config.welcomeMessage != 'undefined');

      var removeElements = function() {
        inner.find('div').each(function() {
          if (!welcome) {
            $(this).remove();
          } else {
            welcome = false;
          }
        });
        inner.find('div.target').each(function() {
          if (!welcome) {
            $(this).remove();
          } else {
            welcome = false;
          }
        });
      };

      if (fadeOnReset) {
        inner.parent().fadeOut(function() {
          removeElements();
          newPromptBox();
          inner.parent().fadeIn(focusConsole);
        });
      } else {
        removeElements();
        newPromptBox();
        focusConsole();
      }
    };

    var focusConsole = function() {
      inner.addClass('jquery-console-focus');
      typer.focus();
    };

    extern.focus = function() {
      focusConsole();
    }

    function newPromptBox() {
      column = 0;
      promptText = '';
      ringn = 0; // Reset the position of the history ring
      enableInput();
      promptBox = $('<div class="jquery-console-prompt-box"></div>');
      var label = $('<span class="jquery-console-prompt-label"></span>');
      var labelText = extern.continuedPrompt ? continuedPromptLabel : extern.promptLabel;
      promptBox.append(label.text(labelText).show());
      label.html(label.html().replace(' ', '&nbsp;'));
      prompt = $('<span class="jquery-console-prompt"></span>');
      promptBox.append(prompt);
      inner.append(promptBox);
      updatePromptDisplay();

      var elmnt = document.getElementById("scrolly");
      elmnt.scrollIntoView();
    };

    // functions for selecting text in prompt area
    function get_focus_offset() {
        var sel;
        if ((sel = window.getSelection()) && (sel.focusNode !== null)) {
            return sel.focusOffset;
        }
    }
    function get_char_pos(e) {
        var focus = get_focus_offset();
        var node = $(e.target);
        if (focus <= node.text().length) {
            var node = $(e.target);
            // [role="presentation"] is my direct children that have
            // siblings that are other nodes with text
            var parent = node.closest('[role="presentation"]');
            var len = node.text().length;
            focus = len === 1 ? 0 : Math.min(focus, len);
            return focus + parent.prevUntil('.prompt').length +
                node.prevAll().length;
        } else {
          return 0;
        }
    }

    // invisible input #box for pasting
    var currentMousePos = { x: -1, y: -1 };
    $(document).mousemove(function(event) {
      currentMousePos.x = event.clientX;
      currentMousePos.y = event.clientY;
      // keep it slightly offset
      if (currentMousePos.y > 0) {
        typer.css('top',event.clientY+30);
        typer.css('left',event.clientX+30);
        typer.css('position', 'absolute');
        typer.css('width', '186px');
        typer.css('opacity', '0.0001');
      }
    });

    // click handler for document
    // we only allow expressly defined clicking from apps who handle link clicks
    $(document).click(function(event) {
      // handle clicking on entry to move cursor
      if (event.target.className == "before") {
        var char_pos = get_char_pos(event);
        var elem_len = $('.before').text().length;
        var offset = elem_len - char_pos;
        moveColumn(-offset);
        updatePromptDisplay();
      } else if (event.target.className == "after") {
        var offset = get_focus_offset();
        moveColumn(offset);
        updatePromptDisplay();
      } else {
        moveToEnd();
      }

      // Don't mess with the focus if there is an active selection
      if (window.getSelection().toString()) {
        return false;
      }
      
      // focus the typer and add the class
      typer.css('position', 'fixed').focus();
      inner.addClass('jquery-console-focus');

      return false;
    });

    // right clicks to typer
    $(document).on("contextmenu", "body", function(e){
      if (window.getSelection().toString()) {
        console.log("window getselection to string");
        return true;
      } else {
        // operate on typer
        inner.removeClass('jquery-console-nofocus');
        inner.addClass('jquery-console-focus');
        // now move it under the cursor
        console.log(currentMousePos.y);
        typer.css('top',currentMousePos.y-13);
        typer.css('left',currentMousePos.x-13);
        typer.css('position', 'absolute');
        typer.css('width', '186px');
        typer.css('position', 'fixed').focus();
        typer.css('opacity', '1%');
        return true;
      }
    });

    // Handle losing focus  (sorta like when you coded this)
    typer.blur(function() {
      inner.removeClass('jquery-console-focus');
      inner.addClass('jquery-console-nofocus');
    });

    // get pasted data
    typer.bind('paste', function(e) {
      // move typer around to ensure we're not scrolling to it
      typer.css('top',currentMousePos.y-13);
      typer.css('left',currentMousePos.x-13);
      typer.css('opacity', '1%');
      typer.css('position', 'absolute');
      typer.css('width', '186px');
      typer.css('opacity', '.0001');

      // wipe typer input clean just in case
      typer.val("");

      // this timeout is required because the onpaste event is
      // fired *before* the text is actually pasted
      setTimeout(function() {
        typer.consoleInsert(typer.val());
        typer.val("");
        var elmnt = document.getElementById("scrolly");
        elmnt.scrollIntoView();

      }, 200);
    });

    // Handle key hit before translation
    typer.keydown(function(e) {
      // quickly move the box under the prompt, thanks Firefox
      // if keycode is ctrl, command (for macOS), shift or alt
      var keyCode = e.keyCode || e.which;

      if (isIgnorableKey(e)) {
        return false;
      }
      config.keydownTrigger(e.keyCode);

      cancelKeyPress = 0;
      var keyCode = e.keyCode;

      // C-c: cancel the execution
      if (e.ctrlKey && keyCode == 67) {
        cancelKeyPress = keyCode;
        cancelExecution();
        return false;
      }
      if (acceptInput) {
        if (e.shiftKey && keyCode in shiftCodes) {
          cancelKeyPress = keyCode;
          (shiftCodes[keyCode])();
          return false;
        } else if (e.altKey && keyCode in altCodes) {
          cancelKeyPress = keyCode;
          (altCodes[keyCode])();
          return false;
        } else if (e.ctrlKey && keyCode in ctrlCodes) {
          cancelKeyPress = keyCode;
          (ctrlCodes[keyCode])();
          return false;
        } else if (keyCode in keyCodes) {
          cancelKeyPress = keyCode;
          (keyCodes[keyCode])();
          return false;
        }
      }
    });

    ////////////////////////////////////////////////////////////////////////
    // Handle key press
    typer.keypress(function(e) {
      var keyCode = e.keyCode || e.which;

      if (isIgnorableKey(e)) {
        return false;
      }

      // C-v: don't insert on paste event
      if ((e.ctrlKey || e.metaKey) && String.fromCharCode(keyCode).toLowerCase() == 'v') {
        return false;
      }
      if (acceptInput && cancelKeyPress != keyCode && keyCode >= 32) {
        if (cancelKeyPress) return false;
        if (
          typeof config.charInsertTrigger == 'undefined' || (
            typeof config.charInsertTrigger == 'function' &&
            config.charInsertTrigger(keyCode, promptText)
          )
        ) {
          typer.consoleInsert(keyCode);
        }
      }
      if (isWebkit) return false;
    });

    // for now just filter alt+tab that we receive on some platforms when
    // user switches windows (goes away from the browser)
    function isIgnorableKey(e) {
      if (e.keyCode == 17 || e.keyCode == 91 || e.keyCode == 16) {
        return true;
      } else if ((e.keyCode == keyCodes.tab || e.keyCode == 192) && e.altKey) {
        return true;
      } else {
        return false;
      }
    };

    ////////////////////////////////////////////////////////////////////////
    // Rotate through the command history
    function rotateHistory(n) {
      if (history.length == 0) return;
      ringn += n;
      if (ringn < 0) ringn = history.length;
      else if (ringn > history.length) ringn = 0;
      var prevText = promptText;
      if (ringn == 0) {
        promptText = restoreText;
      } else {
        promptText = history[ringn - 1];
      }
      if (config.historyPreserveColumn) {
        if (promptText.length < column + 1) {
          column = promptText.length;
        } else if (column == 0) {
          column = promptText.length;
        }
      } else {
        column = promptText.length;
      }
      updatePromptDisplay();
    };

    function getHistory(n) {
      return history[n];
    }

    function previousHistory() {
      rotateHistory(-1);
    };

    // this doesn't work, no idea what's going on
    function clearHistory() {
      alert("history cleared");
      return 0;
    };

    function nextHistory() {
      rotateHistory(1);
    };

    // Add something to the history ring
    function addToHistory(line) {
      if (line != "") {
        history.push(line);
      }
      restoreText = '';
    };

    // get last command
    function getLastCommand() {
      return history[history.length-1];
    };

    // Delete the character at the current position
    function deleteCharAtPos() {
      if (column < promptText.length) {
        promptText =
          promptText.substring(0, column) +
          promptText.substring(column + 1);
        restoreText = promptText;
        return true;
      } else return false;
    };

    function backDelete() {
      if (moveColumn(-1)) {
        deleteCharAtPos();
        updatePromptDisplay();
      }
    };

    function forwardDelete() {
      if (deleteCharAtPos()) {
        updatePromptDisplay();
      }
    };

    function deleteUntilEnd() {
      while (deleteCharAtPos()) {
        updatePromptDisplay();
      }
    };

    function clearCurrentPrompt() {
      extern.promptText("");
    };

    function clearScreen() {
      extern.reset();
    };

    function deleteNextWord() {
      // Delete up to the next alphanumeric character
      while (
        column < promptText.length &&
        !isCharAlphanumeric(promptText[column])
      ) {
        deleteCharAtPos();
        updatePromptDisplay();
      }
      // Then, delete until the next non-alphanumeric character
      while (
        column < promptText.length &&
        isCharAlphanumeric(promptText[column])
      ) {
        deleteCharAtPos();
        updatePromptDisplay();
      }
    };

    function newLine() {
      var lines = promptText.split("\n");
      var last_line = lines.slice(-1)[0];
      var spaces = last_line.match(/^(\s*)/g)[0];
      var new_line = "\n" + spaces;
      promptText += new_line;
      moveColumn(new_line.length);
      updatePromptDisplay();
    };

    // disabled - can be removed
    function commandTrigger() {
      var line = promptText;
      if (typeof config.commandValidate == 'function') {
        var ret = config.commandValidate(line);
        if (ret == true || ret == false) {
          if (ret) {
            handleCommand();
          }
        } else {
          commandResult(ret, "jquery-console-message-error");
        }
      } else {
        handleCommand();
      }
    };
    // end disabled

    function cancelExecution() {
      if (typeof config.cancelHandle == 'function') {
        config.cancelHandle();
      }
    }
    
    function report(msg, className) {
      var text = promptText;
      promptBox.remove();
      commandResult(msg, className);
      extern.promptText(text);
    }

    function message(msg, className) {
      var mesg = $('<div class="jquery-console-message"></div>');
      if (className) {
        mesg.addClass(className);
      }
      mesg.filledText(msg).hide();
      inner.append(mesg);
      mesg.show();
    };

    function updatePromptDisplay() {
      var line = promptText;
      var html = '';
      if (column > 0 && line == '') {
        // When we have an empty line just display a cursor.
        html = cursor;
      } else if (column == promptText.length) {
        // We're at the end of the line, so we need to display
        // the text *and* cursor.
        html = '<span class="before">' + htmlEncode(line) + '</span>' + cursor;
      } else {
        // Grab the current character, if there is one, and
        // make it the current cursor.
        var before = line.substring(0, column);
        var current = line.substring(column, column + 1);
        if (current) {
          current =
            '<span class="jquery-console-cursor">' +
            htmlEncode(current) +
            '</span>';
        }
        var after = line.substring(column + 1);
        html = '<span class="before">' + htmlEncode(before) + '</span>' + current + '<span class="after">' + htmlEncode(after) + '</span>';
      }
      prompt.html(html);
    };

    function commandResult(msg, className) {
      column = -1;
      updatePromptDisplay();
      if (typeof msg == 'string') {
        console.log("string message");
        message(msg, className);
      } else if ($.isArray(msg)) {
        console.log("array message");
        for (var x in msg) {
          var ret = msg[x];

          inner.append(msg);
          message(ret.msg, className);
        }
      } else { // Assume it's a DOM node or jQuery object.
        inner.append(msg);
      }
      newPromptBox();
    };

    function handleCommand() {
      if (typeof config.commandHandle == 'function') {
        disableInput();

        // check history for numeric entry
        var answer_split = promptText.split(" ");
        if (promptText.startsWith("!")) {
          var num_split = answer_split[0].split("!");
          var entry = parseInt(num_split[1]);
          // if it's a number, try to update with the command
          if (!isNaN(entry)) {
            promptText = getHistory(entry);
            if (!promptText) {
              promptText = getHistory(history.length-1)
            }
          }
        }

        addToHistory(promptText);

        var text = promptText;
        
        if (extern.continuedPrompt) {
          if (continuedText)
            continuedText += '\n' + promptText;
          else continuedText = promptText;
        } else continuedText = undefined;
        
        if (continuedText) text = continuedText;
        
        var ret = config.commandHandle(text, function(msgs) {
          commandResult(msgs);
        });

        if (extern.continuedPrompt && !continuedText)
          continuedText = promptText;

        if (typeof ret == 'boolean') {
          if (ret) {
            // Command succeeded without a result.
            commandResult(ret, );
          } else {
            commandResult(
              'Command failed.',
              "jquery-console-message-error"
            );
          }
        } else if (typeof ret == "string") {
          commandResult(ret, "jquery-console-message-success");
        } else if (typeof ret == 'object' && ret.length) {
          commandResult(ret);
        } else if (extern.continuedPrompt) {
          commandResult();
        }
      }
    };

    function disableInput() {
      acceptInput = false;
    };

    function enableInput() {
      acceptInput = true;
    }

    typer.consoleInsert = function(data) {
      var text = (typeof data == 'number') ? String.fromCharCode(data) : data;
      var before = promptText.substring(0, column);
      var after = promptText.substring(column);
      promptText = before + text + after;
      moveColumn(text.length);
      restoreText = promptText;
      updatePromptDisplay();
    };

    function moveColumn(n) {
      if (column + n >= 0 && column + n <= promptText.length) {
        column += n;
        return true;
      } else {
        return false;
      }
    };

    function moveForward() {
      if (moveColumn(1)) {
        updatePromptDisplay();
        return true;
      }
      return false;
    };

    function moveBackward() {
      if (moveColumn(-1)) {
        updatePromptDisplay();
        return true;
      }
      return false;
    };

    function moveToStart() {
      if (moveColumn(-column))
        updatePromptDisplay();
    };

    function moveToEnd() {
      if (moveColumn(promptText.length - column))
        updatePromptDisplay();
    };

    function moveToNextWord() {
      while (
        column < promptText.length &&
        !isCharAlphanumeric(promptText[column]) &&
        moveForward()
      ) {}
      while (
        column < promptText.length &&
        isCharAlphanumeric(promptText[column]) &&
        moveForward()
      ) {}
    };

    function moveToPreviousWord() {
      // Move backward until we find the first alphanumeric
      while (
        column - 1 >= 0 &&
        !isCharAlphanumeric(promptText[column - 1]) &&
        moveBackward()
      ) {}
      // Move until we find the first non-alphanumeric
      while (
        column - 1 >= 0 &&
        isCharAlphanumeric(promptText[column - 1]) &&
        moveBackward()
      ) {}
    };

    function isCharAlphanumeric(charToTest) {
      if (typeof charToTest == 'string') {
        var code = charToTest.charCodeAt();
        return (code >= 'A'.charCodeAt() && code <= 'Z'.charCodeAt()) ||
          (code >= 'a'.charCodeAt() && code <= 'z'.charCodeAt()) ||
          (code >= '0'.charCodeAt() && code <= '9'.charCodeAt());
      }
      return false;
    };

    function doComplete() {
      if (typeof config.completeHandle == 'function') {
        doCompleteDirectly();
      } else {
        issueComplete();
      }
    };

    function doCompleteDirectly() {
      if (typeof config.completeHandle == 'function') {
        var completions = config.completeHandle(promptText);

        var len = completions.length;
        if (len === 1) {
          extern.promptText(promptText + completions[0]);

        } else if (len > 1) {
          var prompt = promptText;
          var completions_string = "system=> Possible commands matching: ";
          var commands_rollup = "";
          $.each(completions, function(index, value){
            var target_id = "target_" + Math.random().toString(36).substring(5,10);

            if (value > "") {
              commands_rollup = commands_rollup + ' <a href id="commands-'+target_id+'">'+prompt+value+'</a>';
              setTimeout(function(){
                $('#commands-'+target_id+'').click(function(){
                  extern.promptText(prompt+value);
                });
              },123);
            }
          });
          var system_reply = $('<div><span class="system_prompt">system=></span> '+commands_rollup+'</div>');
          commandResult(system_reply, "system_prompt");
          extern.promptText(prompt);
        }
      }
    };

    function issueComplete() {
      if (typeof config.completeIssuer == 'function') {
        config.completeIssuer(promptText);
      }
    };

    function decodeHtml(html) {
      return $('<div>').html(html).text();
    }

    extern.promptText = function(text) {
      text = decodeHtml(text);

      if (typeof text === 'string') {
        promptText = text;
        column = promptText.length;
        updatePromptDisplay();
      }
      return promptText;
    };

    // Simple HTML encoding
    // Simply replace '<', '>' and '&'
    // TODO: Use jQuery's .html() trick, or grab a proper, fast
    // HTML encoder.
    function htmlEncode(text) {
      return (
        text.replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/</g, '&lt;')
        .replace(/ /g, '&nbsp;')
        .replace(/\n/g, '<br />')
      );
    };

    return extern;
  };

  // Simple utility for printing messages
  $.fn.filledText = function(txt) {
    $(this).text(txt);
    $(this).html($(this).html().replace(/\n/g, '<br/>').replace(/\s/g, '&nbsp;').replace(/\t/g, '&nbsp;&nbsp;'));
    return this;
  };

})(jQuery);