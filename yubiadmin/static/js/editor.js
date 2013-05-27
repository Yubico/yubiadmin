$(document).ready(function() {
	$.getScript("http://rawgithub.com/ajaxorg/ace-builds/master/src-noconflict/ace.js", function(data, textStatus, jqxhr) {
		$('textarea.editor').each(function() {
			var textarea = $(this);
			var text = textarea.text();
			var div = $('<div />');
			div.width(textarea.width());
			div.height(textarea.height());
			div.text(text);
			var editor = ace.edit(div.get(0));
			textarea.after(div);
			textarea.hide();
			editor.getSession().on('change', function(e) {
				textarea.text(editor.getValue());
			});
		});
	});
});
