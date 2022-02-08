$(function(){
    
    $('.add_atoms').click({div_template: '#usedAtoms-_',
    subfield: '.usedAtoms-subfield',
    div_target: '#usedAtoms-subfield-container',
    class_target: 'usedAtoms-subfield',
    class_template: 'usedAtoms-is-hidden',
    }, addForm)

    $('.add_kendrick').click({div_template: '#kendrickAtoms-_',
                    subfield: '.kendrick-subfield',
                    div_target: '#kendrick-subfield-container',
                    class_target: 'kendrick-subfield',
                    class_template: 'kendrick-is-hidden',
                }, addForm)

    $('.remove_kendrick').click({subfield: '.kendrick-subfield'}, removeForm);
    $('.remove_atoms').click({subfield: '.usedAtoms-subfield'}, removeForm);

});

function adjustIndices(removedIndex, subfield) {
    
    var $forms = $(subfield);

    $forms.each(function(i) {
        var $form = $(this);
        var index = parseInt($form.data('index'));
        var newIndex = index - 1;
        removedIndex
        if (index < removedIndex) {
            // Skip
            return true;
        }

        // Change ID in form itself
        $form.attr('id', $form.attr('id').replace(index, newIndex));
        $form.data('index', newIndex);

        // Change IDs in form inputs
        $form.find('select').each(function(j) {
            var $item = $(this);
            $item.attr('id', $item.attr('id').replace(index, newIndex));
            $item.attr('name', $item.attr('name').replace(index, newIndex));
        });

        $form.find('input').each(function(j) {
            var $item = $(this);
            $item.attr('id', $item.attr('id').replace(index, newIndex));
            $item.attr('name', $item.attr('name').replace(index, newIndex));
        });
    });
}

function removeForm(event) {

    var $removedForm = $(this).closest(event.data.subfield);
    var removedIndex = parseInt($removedForm.data('index'));

    $removedForm.remove();

    // Update indices
    adjustIndices(removedIndex, event.data.subfield);

    // Stops Scrolling Up
    return false;
}

function addForm(event) {
        
    var $templateForm = $(event.data.div_template);
    
    if (!$templateForm) {
        alert('[ERROR] Cannot find template');
        return;
    }

    // Get Last index
    var $lastForm = $(event.data.subfield).last();

    var newIndex = 0;

    if ($lastForm.length > 0) {
        newIndex = parseInt($lastForm.data('index')) + 1;
    }

    // Maximum of 20 subforms
    if (newIndex > 20) {
        alert('[WARNING] Reached maximum number of elements');
        return;
    }

    // Add elements
    var $newForm = $templateForm.clone();

    $newForm.attr('id', $newForm.attr('id').replace('_', newIndex));
    $newForm.attr('data-index', $newForm.attr('data-index').replace('_', newIndex));
    $newForm.data('index', newIndex);

    $newForm.find('input').each(function(idx) {
        var $item = $(this);

        $item.attr('id', $item.attr('id').replace('_', newIndex));
        $item.attr('name', $item.attr('name').replace('_', newIndex));
    });
    
    $newForm.find('select').each(function(idx) {
        var $item = $(this);

        $item.attr('id', $item.attr('id').replace('_', newIndex));
        $item.attr('name', $item.attr('name').replace('_', newIndex));
    });
    
    // Append
    $(event.data.div_target).append($newForm);
    $newForm.addClass(event.data.class_target);
    $newForm.removeClass(event.data.class_template);
    $newForm.find('.remove').click({subfield: event.data.subfield}, removeForm);
    
    // Stops Scrolling Up
    return false;
    
}