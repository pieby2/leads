import { INGESTION_STEPS } from '@/types';

interface ProgressStepperProps {
  currentStep: number;
}

export default function ProgressStepper({ currentStep }: ProgressStepperProps) {
  return (
    <div className="progress-stepper animate-fade-in">
      {INGESTION_STEPS.map((step, index) => {
        const isCompleted = index < currentStep;
        const isActive = index === currentStep;

        return (
          <div className="step-item" key={step.key}>
            <div className="step-node">
              <div
                className={`step-circle ${
                  isCompleted ? 'step-circle-completed' :
                  isActive ? 'step-circle-active' : ''
                }`}
              >
                {isCompleted ? '✓' : index + 1}
              </div>
              <span
                className={`step-label ${
                  isCompleted ? 'step-label-completed' :
                  isActive ? 'step-label-active' : ''
                }`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line (skip after last step) */}
            {index < INGESTION_STEPS.length - 1 && (
              <div className={`step-connector ${isCompleted ? 'step-connector-active' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
