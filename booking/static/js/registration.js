(function () {
  function toStringSet(values) {
    const set = new Set();
    if (!Array.isArray(values)) {
      return set;
    }
    values.forEach(function (value) {
      set.add(String(value));
    });
    return set;
  }

  function normalizeCourseLevels(courseLevels) {
    const normalized = {};
    if (!courseLevels) {
      return normalized;
    }
    Object.keys(courseLevels).forEach(function (key) {
      normalized[String(key)] = courseLevels[key];
    });
    return normalized;
  }

  function uniqueSubjectsForLevels(levels, subjectsByLevel) {
    const seen = new Set();
    const subjects = [];
    levels.forEach(function (level) {
      const entries = subjectsByLevel[level] || [];
      entries.forEach(function (subject) {
        const id = String(subject.id);
        if (seen.has(id)) {
          return;
        }
        seen.add(id);
        subjects.push({ id: id, name: subject.name });
      });
    });
    return subjects;
  }

  function enableToggleMulti(select) {
    if (!select) {
      return;
    }
    select.addEventListener('mousedown', function (event) {
      const option = event.target;
      if (!(option && option.tagName === 'OPTION')) {
        return;
      }
      event.preventDefault();
      option.selected = !option.selected;
      const changeEvent = new Event('change', { bubbles: true });
      select.dispatchEvent(changeEvent);
    });
  }

  function initDynamicRegistrationForm(config) {
    if (!config) {
      return;
    }

    const rolesField = document.querySelector(config.rolesSelector);
    const coursesField = document.querySelector(config.coursesSelector);
    const subjectsField = document.querySelector(config.subjectsSelector);
    const coursesContainer = document.querySelector(config.coursesContainerSelector);
    const subjectsContainer = document.querySelector(config.subjectsContainerSelector);
    const metadata = config.metadata || {};

    if (rolesField) {
      rolesField.multiple = true;
    }
    if (coursesField) {
      coursesField.multiple = true;
    }
    if (subjectsField) {
      subjectsField.multiple = true;
    }

    enableToggleMulti(rolesField);
    enableToggleMulti(coursesField);
    enableToggleMulti(subjectsField);

    if (!rolesField || !coursesField || !subjectsField) {
      return;
    }

    const academicRoleIds = toStringSet(metadata.academic_role_ids || []);
    const courseLevels = normalizeCourseLevels(metadata.course_levels);
    const subjectsByLevel = metadata.subjects_by_level || {};
    const initialSubjectSelection = Array.from(subjectsField.selectedOptions || []).map(function (option) {
      return String(option.value);
    });

    function setContainerVisibility(container, visible) {
      if (!container) {
        return;
      }
      container.hidden = !visible;
    }

    function disableAcademicFields() {
      coursesField.disabled = true;
      subjectsField.disabled = true;
      clearSelections(coursesField);
      clearSelections(subjectsField);
      subjectsField.innerHTML = '';
    }

    function rebuildSubjectOptions(levels) {
      const currentSelection = new Set(Array.from(subjectsField.selectedOptions || []).map(function (option) {
        return String(option.value);
      }));
      const allowedSubjects = uniqueSubjectsForLevels(levels, subjectsByLevel);

      subjectsField.innerHTML = '';

      if (!allowedSubjects.length) {
        subjectsField.disabled = true;
        return;
      }

      allowedSubjects.forEach(function (subject) {
        const option = document.createElement('option');
        option.value = subject.id;
        option.textContent = subject.name;
        if (currentSelection.has(subject.id) || initialSubjectSelection.includes(subject.id)) {
          option.selected = true;
        }
        subjectsField.add(option);
      });
      subjectsField.disabled = false;
    }

    function handleCoursesChange() {
      const selectedLevels = new Set();
      Array.from(coursesField.selectedOptions || []).forEach(function (option) {
        const level = courseLevels[String(option.value)];
        if (level) {
          selectedLevels.add(level);
        }
      });

      if (selectedLevels.size === 0) {
        subjectsField.innerHTML = '';
        subjectsField.disabled = true;
        return;
      }

      rebuildSubjectOptions(Array.from(selectedLevels));
    }

    function handleRolesChange() {
      const selectedRoles = Array.from(rolesField.selectedOptions || []).map(function (option) {
        return String(option.value);
      });
      const requiresAcademicData = selectedRoles.some(function (roleId) {
        return academicRoleIds.has(roleId);
      });

      setContainerVisibility(coursesContainer, requiresAcademicData);
      setContainerVisibility(subjectsContainer, requiresAcademicData);

      if (!requiresAcademicData) {
        disableAcademicFields();
        return;
      }

      coursesField.disabled = false;
      handleCoursesChange();
    }

    rolesField.addEventListener('change', handleRolesChange);
    coursesField.addEventListener('change', handleCoursesChange);

    handleRolesChange();
  }

  window.initDynamicRegistrationForm = initDynamicRegistrationForm;
})();
