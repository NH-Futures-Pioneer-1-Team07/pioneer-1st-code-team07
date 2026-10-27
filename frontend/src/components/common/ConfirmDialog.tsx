import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import styles from "./ConfirmDialog.module.css";

export default function ConfirmDialog({
  title,
  children,
  action,
  onConfirm,
  onClose,
}: {
  title: string;
  children: ReactNode;
  action: string;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    const previous = document.activeElement;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={styles.dialog}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      aria-labelledby="confirm-title"
    >
      <div className={styles.content}>
        <h2 id="confirm-title">{title}</h2>
        <div className={styles.copy}>{children}</div>
        <div className={styles.actions}>
          <button className="button secondary" onClick={onClose} autoFocus>
            돌아가기
          </button>
          <button className="button danger" onClick={onConfirm}>
            {action}
          </button>
        </div>
      </div>
    </dialog>
  );
}
