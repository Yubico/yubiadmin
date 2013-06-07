$(document).ready(function() {
	$('#delete_btn').attr('disabled', 'disabled');

	$('#toggle_all').change(function() {
		$('tbody :checkbox').prop('checked', $(this).is(':checked'));
	});

	$(':checkbox').change(function() {
		if($('tbody :checkbox:checked').length > 0) {
			$('#delete_btn').removeAttr('disabled');
		} else {
			$('#delete_btn').attr('disabled', 'disabled');
		}
	});

	if($('tbody :checkbox:checked').length > 0) {
		$('#delete_btn').removeAttr('disabled');
	}
});
