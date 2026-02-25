if (!window.dash_clientside) {
    window.dash_clientside = {};
}

if (!window.dash_clientside.clientside) {
    window.dash_clientside.clientside = {};
}

Object.assign(window.dash_clientside.clientside, {
    display_if_loops: function (testType) {
        if (!testType) return { 'display': 'none' };
        return (testType === 'Loops') ? { 'display': 'block' } : { 'display': 'none' };
    },
    display_if_sweep: function (testType) {
        if (!testType) return { 'display': 'none' };
        return (testType === 'Sweep' || testType === 'Shmoo') ? { 'display': 'block' } : { 'display': 'none' };
    },
    display_if_linux: function (content) {
        if (!content) return { 'display': 'none' };
        return (content === 'Linux') ? { 'display': 'block' } : { 'display': 'none' };
    },
    display_if_dragon: function (content) {
        if (!content) return { 'display': 'none' };
        return (content === 'Dragon') ? { 'display': 'block' } : { 'display': 'none' };
    },
    display_if_custom: function (script) {
        if (!script) return { 'display': 'none' };
        return (script === 'Custom') ? { 'display': 'block' } : { 'display': 'none' };
    }
});
