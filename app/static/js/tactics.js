var edit_flag = false;

// Index of lines that are read-only.
var readonly_lines = [0];

// Line number for the currently selected goal.
// -1 for no goal selected.
var click_line_number = -1;

// Line number for the currently selected conclusion.
// -1 for no conclusion selected.
var ctrl_click_line_number = -1;

// Currently edited line. -1 for not currently editing.
var edit_line_number = -1;

// Current proof content in all of the tabs.
// Maintained as a dictionary. Keys are ids for the textarea.
// Values are the corresponding proof content.
var cells = {};

// Mode for displaying proof
// 显示证明的模式
// 0 - 显示所有内容。 1 - 只显示id和thm。
var mod = 0;

function get_selected_id() {
    return document.querySelector('.code-cell.selected textarea').id;
}

function get_selected_editor() {
    return document.querySelector('.code-cell.selected textarea + .CodeMirror').CodeMirror;
}

function get_selected_output() {
    return document.querySelector('.code-cell.selected .output pre');
}

function get_selected_instruction() {
    return document.querySelector('.code-cell.selected .output #instruction');
}

function get_selected_instruction_number() {
    return document.querySelector('.code-cell.selected .output #instruction-number');
}

function display_running() {
    var status_output = get_selected_output();
    status_output.innerHTML = "Running";
}

// Display result returned from the server.
function display_checked_proof(result) {
    var status_output = get_selected_output();

    if ("failed" in result) {
        status_output.innerHTML = result["failed"] + ": " + result["message"];
        status_output.style.color = 'red';
    } else {
        edit_line_number = -1;
        id = get_selected_id();
        cells[id] = {};
        cells[id]['proof'] = result['proof'];
        display(id);
        var num_gaps = result["report"]["num_gaps"];
        cells[id]['num_gaps'] = num_gaps;
        status_output.style.color = '';
        if (num_gaps > 0) {
            status_output.innerHTML = "OK. " + num_gaps + " gap(s) remaining."
        } else {
            status_output.innerHTML = "OK. Proof complete!"
        }
    }
}

function display_instuctions(instructions) {
    var instr_output = get_selected_instruction();
    instr_output.innerHTML = instructions[0];
    var instr_no_output = get_selected_instruction_number();
    instr_no_output.innerHTML = '1/' + instructions.length;
}

function add_line_after(cm) {
    $(document).ready(function () {
        var id = get_selected_id();
        var line_number = cm.getCursor().line;
        var input = {
            "id": id,
            "line_id": cells[id]['proof'][line_number]['id'],
        };
        var data = JSON.stringify(input);
        display_running();

        $.ajax({
            url: "/api/add-line-after",
            type: "POST",
            data: data,
            success: function (result) {
                display_checked_proof(result);
                cm.setCursor(line_number + 1, Number.MAX_SAFE_INTEGER);
            }
        })
    })
}

function remove_line(cm) {
    $(document).ready(function () {
        var id = get_selected_id();
        var line_number = cm.getCursor().line;
        var input = {
            "id": id,
            "line_id": cells[id]['proof'][line_number]['id'],
        };
        var data = JSON.stringify(input);
        display_running();

        $.ajax({
            url: "/api/remove-line",
            type: "POST",
            data: data,
            success: function (result) {
                display_checked_proof(result);
                cm.setCursor(line_number - 1, Number.MAX_SAFE_INTEGER);
            }
        })
    })
}

function introduction(cm) {
    $(document).ready(function () {
        var id = get_selected_id();
        var line_number = cm.getCursor().line;
        var line = cm.getLine(line_number);
        var input = {
            "id": id,
            "line_id": cells[id]['proof'][line_number]['id'],
        };

        if (line.indexOf("⊢ ∀") !== -1) {
            input["var_name"] = prompt('Enter variable name').split(",")
        }
        var data = JSON.stringify(input);
        display_running();

        $.ajax({
            url: "/api/introduction",
            type: "POST",
            data: data,
            success: function (result) {
                display_checked_proof(result);
                cm.setCursor(line_number + result['line-diff'], Number.MAX_SAFE_INTEGER);
            }
        })
    })
}

function apply_backward_step(cm) {
    var title = '';
    if (click_line_number !== -1 && ctrl_click_line_number !== -1) {
        title = 'Target: ' + (click_line_number + 1) + '\nConclusion: ' + (ctrl_click_line_number + 1);
        line = cm.getLine(click_line_number);
    } else if (click_line_number !== -1 && ctrl_click_line_number === -1) {
        title = 'Target: ' + (click_line_number + 1);
    } else {
        title = 'Please enter the theorem userd';
    }
    swal({
        title: title,
        html:
            '<input id="swal-input1" class="swal2-input">',
        showCancelButton: true,
        confirmButtonText: 'confirm',
        showLoaderOnConfirm: true,
        focusConfirm: false,
        preConfirm: () => {
            document.querySelector('#swal-input1').focus();
            var id = '';
            var theorem = '';
            if (click_line_number !== -1 && ctrl_click_line_number !== -1) {
                id = cells[get_selected_id()]['proof'][ctrl_click_line_number]['id'];
                theorem = document.getElementById('swal-input1').value + ', ' + id;
            } else if (click_line_number !== -1 && ctrl_click_line_number === -1) {
                theorem = document.getElementById('swal-input1').value;
            }
            var data = {
                'id': get_selected_id(),
                'line_id': cells[get_selected_id()]['proof'][click_line_number]['id'],
                'theorem': theorem,
            };
            return fetch('/api/apply-backward-step', {
                    method: 'POST', // or 'PUT'
                    body: JSON.stringify(data),
                    headers: {
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                    },
                }
            ).then(response => {
                if (!response.ok) {
                    throw new Error(response.statusText)
                }
                return response.json()
            })
                .catch(error => {
                    swal.showValidationMessage(
                        `Request failed: ${error}`
                    )
                })
        },
        allowOutsideClick:
            () => !swal.isLoading()
    }).then((result) => {
        if (result) {
            click_line_number = -1;
            ctrl_click_line_number = -1;
            display_checked_proof(result['value']);
        }
    })
}

function apply_induction(cm) {
    $(document).ready(function () {
        var line_no = cm.getCursor().line;
        var id = get_selected_id();
        var input = {
            'id': id,
            'line_id': cells[id]['proof'][line_no]['id']
        };

        input['theorem'] = prompt('Enter induction theorem and variable name');
        var data = JSON.stringify(input);
        display_running();

        $.ajax({
            url: "/api/apply-induction",
            type: "POST",
            data: data,
            success: function (result) {
                display_checked_proof(result);
            }
        })
    })
}

function rewrite_goal(cm) {
    $(document).ready(function () {
        var line_no = cm.getCursor().line;
        var id = get_selected_id();
        var input = {
            'id': id,
            'line_id': cells[id]['proof'][line_no]['id']
        };

        input['theorem'] = prompt('Enter rewrite theorem');
        var data = JSON.stringify(input);
        display_running();

        $.ajax({
            url: "/api/rewrite-goal",
            type: "POST",
            data: data,
            success: function (result) {
                display_checked_proof(result);
            }
        })
    })
}

function set_line(cm) {
    $(document).ready(function () {
        var line = cm.getLine(edit_line_number);
        var input = {
            'id': get_selected_id(),
            'line': line
        };
        var data = JSON.stringify(input);
        display_running();

        $.ajax({
            url: "/api/set-line",
            type: "POST",
            data: data,
            success: function (result) {
                display_checked_proof(result);
            }
        })
    })
}

// Print string without highlight at given line_no and ch. Return the new value of ch.
function display_str(editor, str, line_no, ch, mark) {
    len = str.length;
    editor.replaceRange(str, {line: line_no, ch: ch}, {line: line_no, ch: ch + len});
    if (typeof mark !== 'undefined') {
        editor.markText({line: line_no, ch: ch}, {line: line_no, ch: ch + len}, mark);
    } 
    return ch + len;
}

// Print string with highlight at given line_no and ch.
// p[0] is the printed string, p[1] is the color.
// Return the new value of ch.
function display_highlight_str(editor, p, line_no, ch) {
    var color;
    if (p[1] === 0)
        color = "color: black";
    else if (p[1] === 1)
        color = "color: green";
    else if (p[1] === 2)
        color = "color: blue";
    return display_str(editor, p[0], line_no, ch, {css: color});
}

// Display a list of pairs with highlight
function display_highlight_strs(editor, ps, line_no, ch) {
    $.each(ps, function(i, p) {
        ch = display_highlight_str(editor, p, line_no, ch);
    })
    return ch;
}

// Print a single line.
function display_line(id, line_no) {
    var editor = get_selected_editor();
    var line = cells[id]['proof'][line_no];
    var ch = 0;

    edit_flag = true;
    // Display id in bold
    ch = display_str(editor, line.id + ': ', line_no, ch, {css: 'font-weight: bold'});
    // Display theorem with highlight
    if (line.th.length > 0) {
        ch = display_highlight_strs(editor, line.th, line_no, ch);
        ch = display_str(editor, ' by ', line_no, ch, {css: 'font-weight: bold'});
    }
    // Display rule name
    ch = display_str(editor, line.rule, line_no, ch);
    // Display args with highlight
    if (line.args.length > 0) {
        ch = display_str(editor, ' ', line_no, ch);
        ch = display_highlight_strs(editor, line.args, line_no, ch);
    }
    if (line.prevs.length > 0) {
        ch = display_str(editor, ' from ', line_no, ch, {css: 'font-weight: bold'});
        ch = display_str(editor, line.prevs.join(', '), line_no, ch);
    }
    edit_flag = false;
}

// Display the given content in the textarea with the given id.
function display(id) {
    var editor = get_selected_editor();
    edit_flag = true;
    editor.setValue('');
    edit_flag = false;
    var cell = cells[id]['proof'];
    $.each(cell, function(line_no) {
        display_line(id, line_no);
        edit_flag = true;
        var len = editor.getLineHandle(line_no).text.length;
        editor.replaceRange('\n', {line: line_no, ch: len}, {line: line_no, ch: len + 1});
        edit_flag = false;
    })

    readonly_lines.length = 0;
    for (var i = 0; i < editor.lineCount(); i++)
        readonly_lines.push(i);
}
