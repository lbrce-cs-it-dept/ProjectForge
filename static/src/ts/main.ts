import {
  createIcons,
  Eye,
  EyeOff,
} from "lucide";

/* =========================================================
   PASSWORD VISIBILITY
   ========================================================= */

const passwordToggles =
  document.querySelectorAll<HTMLButtonElement>(
    "[data-password-toggle]",
  );

passwordToggles.forEach((toggle) => {
  const inputId =
    toggle.dataset.passwordToggle;

  if (!inputId) {
    return;
  }

  const input =
    document.getElementById(
      inputId,
    ) as HTMLInputElement | null;

  if (!input) {
    return;
  }

  toggle.addEventListener(
    "click",
    () => {
      const isPassword =
        input.type === "password";

      input.type =
        isPassword
          ? "text"
          : "password";

      toggle.setAttribute(
        "aria-label",
        isPassword
          ? "Hide password"
          : "Show password",
      );

      toggle.setAttribute(
        "title",
        isPassword
          ? "Hide password"
          : "Show password",
      );

      toggle.innerHTML =
        isPassword
          ? '<i data-lucide="eye-off"></i>'
          : '<i data-lucide="eye"></i>';

      createIcons({
        icons: {
          Eye,
          EyeOff,
        },
      });
    },
  );
});

/*
 * Login page uses the legacy IDs.
 * Keep them supported so the existing login
 * markup continues to work.
 */
const loginPasswordInput =
  document.querySelector<HTMLInputElement>(
    "#password",
  );

const loginPasswordToggle =
  document.querySelector<HTMLButtonElement>(
    "#password-toggle",
  );

if (
  loginPasswordInput &&
  loginPasswordToggle
) {
  loginPasswordToggle.dataset.passwordToggle =
    loginPasswordInput.id;
}

createIcons({
  icons: {
    Eye,
    EyeOff,
  },
});

/* =========================================================
   DELETE SCROLL POSITION
   ========================================================= */

const deleteScrollStorageKey =
  "projectforge-delete-scroll-position";

history.scrollRestoration = "manual";

const saveDeleteScrollPosition = () => {
  sessionStorage.setItem(
    deleteScrollStorageKey,
    JSON.stringify({
      path: window.location.pathname,
      scrollY: window.scrollY,
    }),
  );
};

const getSavedDeleteScrollPosition = (): {
  path: string;
  scrollY: number;
} | null => {
  const storedPosition =
    sessionStorage.getItem(
      deleteScrollStorageKey,
    );

  if (!storedPosition) {
    return null;
  }

  try {
    const parsed: unknown =
      JSON.parse(storedPosition);

    if (
      typeof parsed !== "object" ||
      parsed === null
    ) {
      return null;
    }

    if (
      !("path" in parsed) ||
      !("scrollY" in parsed)
    ) {
      return null;
    }

    const path = parsed.path;
    const scrollY = parsed.scrollY;

    if (
      typeof path !== "string" ||
      typeof scrollY !== "number"
    ) {
      return null;
    }

    return {
      path,
      scrollY,
    };
  } catch {
    return null;
  }
};

const restoreDeleteScrollPosition = () => {
  const savedPosition =
    getSavedDeleteScrollPosition();

  if (!savedPosition) {
    return;
  }

  if (
    savedPosition.path !==
    window.location.pathname
  ) {
    sessionStorage.removeItem(
      deleteScrollStorageKey,
    );

    return;
  }

  const targetScrollY =
    savedPosition.scrollY;

  let attempts = 0;

  const restore = () => {
    attempts += 1;

    const maximumScrollY =
      document.documentElement.scrollHeight -
      window.innerHeight;

    const scrollY = Math.min(
      targetScrollY,
      Math.max(0, maximumScrollY),
    );

    window.scrollTo(
      0,
      scrollY,
    );

    const currentScrollY =
      window.scrollY;

    if (
      Math.abs(
        currentScrollY - scrollY,
      ) <= 2
    ) {
      sessionStorage.removeItem(
        deleteScrollStorageKey,
      );

      return;
    }

    if (attempts < 20) {
      window.setTimeout(
        restore,
        50,
      );

      return;
    }

    sessionStorage.removeItem(
      deleteScrollStorageKey,
    );
  };

  window.setTimeout(
    restore,
    50,
  );
};

if (document.readyState === "loading") {
  window.addEventListener(
    "load",
    restoreDeleteScrollPosition,
    {
      once: true,
    },
  );
} else {
  restoreDeleteScrollPosition();
}

/* =========================================================
   ALL DELETE FORMS
   ========================================================= */

const deleteForms =
  document.querySelectorAll<HTMLFormElement>(
    'form[action*="/delete/"]',
  );

deleteForms.forEach((form) => {
  form.addEventListener(
    "submit",
    () => {
      saveDeleteScrollPosition();
    },
  );
});

/* =========================================================
   PROJECT DELETE MODAL
   ========================================================= */

const projectDeleteModal =
  document.querySelector<HTMLElement>(
    "#delete-project-modal",
  );

const projectDeleteOpenButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-project-button",
  );

const projectDeleteCloseButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-modal-close",
  );

const projectDeleteCancelButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-modal-cancel",
  );

const projectDeleteBackdrop =
  document.querySelector<HTMLElement>(
    "#delete-modal-backdrop",
  );

const openProjectDeleteModal = () => {
  if (!projectDeleteModal) {
    return;
  }

  projectDeleteModal.hidden = false;
  document.body.classList.add("modal-open");

  projectDeleteCloseButton?.focus();
};

const closeProjectDeleteModal = () => {
  if (!projectDeleteModal) {
    return;
  }

  projectDeleteModal.hidden = true;
  document.body.classList.remove("modal-open");

  projectDeleteOpenButton?.focus();
};

projectDeleteOpenButton?.addEventListener(
  "click",
  openProjectDeleteModal,
);

projectDeleteCloseButton?.addEventListener(
  "click",
  closeProjectDeleteModal,
);

projectDeleteCancelButton?.addEventListener(
  "click",
  closeProjectDeleteModal,
);

projectDeleteBackdrop?.addEventListener(
  "click",
  closeProjectDeleteModal,
);

/* =========================================================
   MILESTONE DELETE MODAL
   ========================================================= */

const milestoneDeleteModal =
  document.querySelector<HTMLElement>(
    "#delete-milestone-modal",
  );

const milestoneDeleteButtons =
  document.querySelectorAll<HTMLButtonElement>(
    ".milestone-delete-button",
  );

const milestoneDeleteCloseButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-milestone-modal-close",
  );

const milestoneDeleteCancelButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-milestone-modal-cancel",
  );

const milestoneDeleteBackdrop =
  document.querySelector<HTMLElement>(
    "#delete-milestone-modal-backdrop",
  );

const milestoneDeleteName =
  document.querySelector<HTMLElement>(
    "#delete-milestone-name",
  );

const milestoneDeleteForm =
  document.querySelector<HTMLFormElement>(
    "#delete-milestone-form",
  );

const openMilestoneDeleteModal = (
  button: HTMLButtonElement,
) => {
  if (
    !milestoneDeleteModal ||
    !milestoneDeleteName ||
    !milestoneDeleteForm
  ) {
    return;
  }

  const milestoneId =
    button.dataset.milestoneId;

  const milestoneTitle =
    button.dataset.milestoneTitle;

  if (!milestoneId || !milestoneTitle) {
    return;
  }

  milestoneDeleteName.textContent =
    `"${milestoneTitle}"`;

  const currentPath =
    window.location.pathname;

  const projectPath =
    currentPath
      .split("/milestones/")[0]
      .replace(/\/+$/, "");

  milestoneDeleteForm.action =
    `${projectPath}/milestones/${milestoneId}/delete/`;

  milestoneDeleteModal.hidden = false;
  document.body.classList.add("modal-open");

  milestoneDeleteCloseButton?.focus();
};

const closeMilestoneDeleteModal = () => {
  if (!milestoneDeleteModal) {
    return;
  }

  milestoneDeleteModal.hidden = true;
  document.body.classList.remove("modal-open");
};

milestoneDeleteButtons.forEach((button) => {
  button.addEventListener("click", () => {
    openMilestoneDeleteModal(button);
  });
});

milestoneDeleteCloseButton?.addEventListener(
  "click",
  closeMilestoneDeleteModal,
);

milestoneDeleteCancelButton?.addEventListener(
  "click",
  closeMilestoneDeleteModal,
);

milestoneDeleteBackdrop?.addEventListener(
  "click",
  closeMilestoneDeleteModal,
);

/* =========================================================
   TASK DELETE MODAL
   ========================================================= */

const taskDeleteModal =
  document.querySelector<HTMLElement>(
    "#delete-task-modal",
  );

const taskDeleteButtons =
  document.querySelectorAll<HTMLButtonElement>(
    ".task-delete-button",
  );

const taskDeleteCloseButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-task-modal-close",
  );

const taskDeleteCancelButton =
  document.querySelector<HTMLButtonElement>(
    "#delete-task-modal-cancel",
  );

const taskDeleteBackdrop =
  document.querySelector<HTMLElement>(
    "#delete-task-modal-backdrop",
  );

const taskDeleteName =
  document.querySelector<HTMLElement>(
    "#delete-task-name",
  );

const taskDeleteForm =
  document.querySelector<HTMLFormElement>(
    "#delete-task-form",
  );

const openTaskDeleteModal = (
  button: HTMLButtonElement,
) => {
  if (
    !taskDeleteModal ||
    !taskDeleteName ||
    !taskDeleteForm
  ) {
    return;
  }

  const taskTitle =
    button.dataset.taskTitle;

  const deleteUrl =
    button.dataset.taskDeleteUrl;

  if (!taskTitle || !deleteUrl) {
    return;
  }

  taskDeleteName.textContent =
    `"${taskTitle}"`;

  taskDeleteForm.action =
    deleteUrl;

  taskDeleteModal.hidden = false;
  document.body.classList.add("modal-open");

  taskDeleteCloseButton?.focus();
};

const closeTaskDeleteModal = () => {
  if (!taskDeleteModal) {
    return;
  }

  taskDeleteModal.hidden = true;
  document.body.classList.remove("modal-open");
};

taskDeleteButtons.forEach((button) => {
  button.addEventListener("click", () => {
    openTaskDeleteModal(button);
  });
});

taskDeleteCloseButton?.addEventListener(
  "click",
  closeTaskDeleteModal,
);

taskDeleteCancelButton?.addEventListener(
  "click",
  closeTaskDeleteModal,
);

taskDeleteBackdrop?.addEventListener(
  "click",
  closeTaskDeleteModal,
);

/* =========================================================
   ESCAPE KEY
   ========================================================= */

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") {
    return;
  }

  if (
    projectDeleteModal &&
    !projectDeleteModal.hidden
  ) {
    closeProjectDeleteModal();
    return;
  }

  if (
    milestoneDeleteModal &&
    !milestoneDeleteModal.hidden
  ) {
    closeMilestoneDeleteModal();
    return;
  }

  if (
    taskDeleteModal &&
    !taskDeleteModal.hidden
  ) {
    closeTaskDeleteModal();
  }
});
