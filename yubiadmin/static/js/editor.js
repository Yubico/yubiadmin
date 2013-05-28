$(document).ready(function() {
	$.ajaxSetup({cache: true});
	$.getScript("/js/ace/ace.js", function(data, textStatus, jqxhr) {
		ace.config.set("modePath", "/js/ace/");
		ace.config.set("workerPath", "/js/ace/");
		ace.config.set("themePath", "/js/ace/");
		$('textarea.editor').each(function() {
			var textarea = $(this);
			var text = textarea.text();
			var div = $('<div />');
			div.width(textarea.width());
			div.height(textarea.height());
			div.text(text);
			var editor = ace.edit(div.get(0));
			editor.setTheme('ace/theme/chrome');
			textarea.closest('form').bind('reset', function() {
				editor.setValue(text);
				editor.gotoLine(0);
			});
			var mode = textarea.attr('ace-mode');
			if(mode) {
				editor.getSession().setMode('ace/mode/'+mode);
			}
			textarea.after(div);
			textarea.hide();
			editor.getSession().on('change', function(e) {
				textarea.text(editor.getValue());
			});
		});
	});
});
