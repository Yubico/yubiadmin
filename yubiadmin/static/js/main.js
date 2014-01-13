$(document).ready(function() {
	$('body').on('click', '.selectable-text', function() {
		if (document.body.createTextRange) {
			var range = document.body.createTextRange();
			range.moveToElementText(this);
			range.select();
		} else if (window.getSelection) {
			var selection = window.getSelection();        
			var range = document.createRange();
			range.selectNodeContents(this);
			selection.removeAllRanges();
			selection.addRange(range);
		}
	});
});
