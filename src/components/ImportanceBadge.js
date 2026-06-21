import React from 'react';
import { scoreImportance, IMPORTANCE_STYLES, IMPORTANCE_LABELS } from '../utils/importance';

const ImportanceBadge = ({ item }) => {
  const level = scoreImportance(item);
  return (
    <span
      className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border shrink-0 ${IMPORTANCE_STYLES[level]}`}
      title={`Poziom istotności: ${IMPORTANCE_LABELS[level]}`}
    >
      {IMPORTANCE_LABELS[level]}
    </span>
  );
};

export default ImportanceBadge;
