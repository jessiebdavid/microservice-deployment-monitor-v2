import {

  useEffect,

  useRef,

  useState,

  type CSSProperties,
  type PointerEvent as ReactPointerEvent,

  type ReactNode,

} from 'react'



import {

  createDeployment,

  getDeploymentValidations,

} from './services/api'



import type {

  Deployment,

  ValidationResult,

} from './types/deployment'



import {

  Activity,

  ArrowRight,

  Box,

  Check,

  HeartPulse,

  LayoutDashboard,

  LoaderCircle,

  Rocket,

  Settings,

  ShieldCheck,

  SlidersHorizontal,

} from 'lucide-react'



import './App.css'



/* =========================================================

   TYPES

   ========================================================= */



type PageName =

  | 'Overview'

  | 'Deployments'

  | 'Services'

  | 'Governance'

  | 'Configuration'

  | 'Health'

  | 'Settings'



/* =========================================================

   NAVIGATION

   ========================================================= */



const navigation: {

  label: PageName

  icon: typeof LayoutDashboard

}[] = [

  {

    label: 'Overview',

    icon: LayoutDashboard,

  },

  {

    label: 'Deployments',

    icon: Rocket,

  },

  {

    label: 'Services',

    icon: Box,

  },

  {

    label: 'Governance',

    icon: ShieldCheck,

  },

  {

    label: 'Configuration',

    icon: SlidersHorizontal,

  },

  {

    label: 'Health',

    icon: HeartPulse,

  },

  {

    label: 'Settings',

    icon: Settings,

  },

]



/* =========================================================

   LOADING STEPS

   ========================================================= */



const loadingSteps = [

  'Loading deployment monitor',

  'Connecting governance engine',

  'Loading configuration validator',

  'Connecting health checker',

  'Initializing result aggregator',

]



/* =========================================================

   APP

   ========================================================= */



const runtimeStyles = `
.context-content {
  position: relative;
  z-index: 2;
}

.context-grid {
  width: min(980px, 100%);
  margin: 24px auto 0;
}

.settings-grid,
.service-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.context-card {
  min-height: 92px;
}

.context-card strong {
  display: block;
  margin-top: 10px;
  line-height: 1.35;
}

.context-value-wrap {
  overflow-wrap: anywhere;
}

.context-validation-card {
  width: min(980px, 100%);
  margin: 18px auto 0;
  padding: 22px;
  border-radius: 18px;
  text-align: left;
  box-sizing: border-box;
}

.context-validation-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.context-validation-header h3 {
  margin: 8px 0 0;
  font-size: 17px;
  line-height: 1.35;
}

.context-validation-details {
  margin: 14px 0 0;
  color: rgba(255,255,255,.58);
  font-size: 12px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.context-muted {
  margin: 14px 0 0;
  color: rgba(255,255,255,.38);
  font-size: 12px;
  line-height: 1.6;
}

.context-status {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 68px;
  padding: 7px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,.08);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .12em;
}

.context-status.pass,
.context-status.online {
  color: #65f5df;
  background: rgba(56,239,214,.09);
  border-color: rgba(101,245,223,.15);
}

.context-status.fail {
  color: #ff718d;
  background: rgba(255,82,120,.09);
  border-color: rgba(255,82,120,.15);
}

.context-status.warn {
  color: #f5cf72;
  background: rgba(245,207,114,.09);
  border-color: rgba(245,207,114,.15);
}

.context-status.skipped,
.context-status.idle {
  color: rgba(255,255,255,.48);
  background: rgba(255,255,255,.04);
}

.settings-note {
  margin-top: 18px;
}

@media (max-width: 900px) {
  .settings-grid,
  .service-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .context-validation-header {
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .settings-grid,
  .service-grid {
    grid-template-columns: 1fr;
  }

  .context-validation-card {
    padding: 18px;
  }
}
`

function App() {

  const [activePage, setActivePage] =

    useState<PageName>('Overview')



  const [switching, setSwitching] =

    useState(false)



  const [loadingStep, setLoadingStep] =

    useState(0)


  const [latestDeployment, setLatestDeployment] =

    useState<Deployment | null>(null)

  const [latestValidations, setLatestValidations] =

    useState<ValidationResult[]>([])



  useEffect(() => {
    try {
      const savedDeployment =
        window.localStorage.getItem(
          'deployguard.latestDeployment',
        )

      const savedValidations =
        window.localStorage.getItem(
          'deployguard.latestValidations',
        )

      if (savedDeployment) {
        setLatestDeployment(
          JSON.parse(savedDeployment) as Deployment,
        )
      }

      if (savedValidations) {
        setLatestValidations(
          JSON.parse(savedValidations) as ValidationResult[],
        )
      }
    } catch {
      window.localStorage.removeItem(
        'deployguard.latestDeployment',
      )
      window.localStorage.removeItem(
        'deployguard.latestValidations',
      )
    }
  }, [])

const handleDeploymentComplete = (
    deployment: Deployment,
    validations: ValidationResult[],
  ) => {
    setLatestDeployment(deployment)
    setLatestValidations(validations)

    window.localStorage.setItem(
      'deployguard.latestDeployment',
      JSON.stringify(deployment),
    )

    window.localStorage.setItem(
      'deployguard.latestValidations',
      JSON.stringify(validations),
    )
  }



  const switchPage = (page: PageName) => {

    if (

      page === activePage ||

      switching

    ) {

      return

    }



    setLoadingStep(0)

    setSwitching(true)



    let step = 0



    const timer = window.setInterval(() => {

      step += 1



      setLoadingStep(

        Math.min(

          step,

          loadingSteps.length - 1,

        ),

      )



      if (

        step >=

        loadingSteps.length - 1

      ) {

        window.clearInterval(timer)



        window.setTimeout(() => {

          setActivePage(page)

          setSwitching(false)

        }, 650)

      }

    }, 260)

  }



  return (

    <main className="command-center">

      <Background />

      <style>{runtimeStyles}</style>



      {/* =================================================

          ACTIVE PAGE

          ================================================= */}



      {activePage === 'Overview' ? (

        <OverviewPage
          onInitialize={() => switchPage('Deployments')}
          latestDeployment={latestDeployment}
        />

      ) : (

        <ContextPage

          page={activePage}

          latestDeployment={latestDeployment}

          latestValidations={latestValidations}

          onOpenDeployments={() => switchPage('Deployments')}

          onDeploymentComplete={handleDeploymentComplete}

        />

      )}



      {/* =================================================

          BOTTOM NAVIGATION

          ================================================= */}



      <nav className="bottom-dock glass">

        {navigation.map((item) => {

          const Icon = item.icon



          const active =

            activePage === item.label



          return (

            <button

              key={item.label}

              className={`dock-item ${

                active ? 'active' : ''

              }`}

              onClick={() =>

                switchPage(item.label)

              }

            >

              <span className="dock-icon">

                <Icon

                  size={18}

                  strokeWidth={1.8}

                />

              </span>



              <span className="dock-label">

                {item.label}

              </span>



              <span className="dock-ripple" />

            </button>

          )

        })}

      </nav>



      {/* =================================================

          CONTEXT TRANSITION

          ================================================= */}



      {switching && (

        <div className="context-transition">

          <LoadingScreen

            currentStep={loadingStep}

            totalSteps={

              loadingSteps.length

            }

          />

        </div>

      )}

    </main>

  )

}



/* =========================================================

   OVERVIEW PAGE

   ========================================================= */



function OverviewPage({

  onInitialize,

  latestDeployment,

}: {

  onInitialize: () => void

  latestDeployment: Deployment | null
}) {

  const handleExplore = () => {
    document
      .querySelector('.product-section')
      ?.scrollIntoView({ behavior: 'smooth' })
  }

  const deployments = latestDeployment ? '1' : '0'
  const passed = latestDeployment?.status === 'SUCCESS' ? '1' : '0'
  const failed = latestDeployment?.status === 'FAILED' ? '1' : '0'
  const running =
    latestDeployment &&
    (latestDeployment.status === 'PENDING' ||
      latestDeployment.status === 'VALIDATING')
      ? '1'
      : '0'

  return (

    <div className="overview-page">

      <CommandHeader />



      {/* =================================================

          HERO

          ================================================= */}



      <section className="hero-section">

        <div className="hero-content">

          <div className="hero-eyebrow">

            DEPLOYMENT INTELLIGENCE PLATFORM

          </div>



          <h1 className="hero-title">

            Deploy with

            <span>

              confidence.

            </span>

          </h1>



          <p className="hero-description">

            Validate governance, configuration and

            service health before your deployment

            moves forward.

          </p>



          <div className="hero-actions">

            <button
              className="hero-primary magnetic"
              onClick={onInitialize}
            >

              <Rocket size={16} />

              Initialize Deployment

            </button>



            <button
              className="hero-secondary magnetic"
              onClick={handleExplore}
            >

              Explore Platform

              <ArrowRight size={16} />

            </button>

          </div>



          <div className="ready-state">

            <span className="ready-dot" />

            Validation systems ready

          </div>



          <div className="hero-metrics glass interactive-surface">

            <Metric

              value={deployments}

              label="Session deployments"

            />



            <Metric

              value={passed}

              label="Passed"

            />



            <Metric

              value={failed}

              label="Failed"

            />



            <Metric

              value={running}

              label="Running"

            />

          </div>

        </div>



        <OrbitalSystem />

      </section>



      <div className="scroll-indicator">

        <span>

          SCROLL TO EXPLORE

        </span>



        <ArrowRight size={14} />

      </div>



      {/* =================================================

          WHAT IS DEPLOYGUARD

          ================================================= */}



      <section className="product-section">

        <div className="product-intro">

          <div className="section-eyebrow">

            WHAT IS DEPLOYGUARD

          </div>



          <h2>

            A smarter way to

            <span>

              deploy software.

            </span>

          </h2>



          <p>

            DeployGuard brings deployment validation

            into one coordinated flow. It checks

            governance, configuration and service

            health before producing a final

            deployment result.

          </p>



          <button
            className="learn-button magnetic"
            onClick={() =>
              document
                .querySelector('.flow-section')
                ?.scrollIntoView({ behavior: 'smooth' })
            }
          >

            Explore the workflow

            <ArrowRight size={15} />

          </button>

        </div>



        <div className="feature-grid">

          <FeatureCard

            number="01"

            icon={

              <ShieldCheck size={19} />

            }

            title="Governance"

            description="Validate policies, rules and deployment requirements."

            accent="cyan"

          />



          <FeatureCard

            number="02"

            icon={

              <SlidersHorizontal

                size={19}

              />

            }

            title="Configuration"

            description="Check required deployment settings and configuration."

            accent="violet"

          />



          <FeatureCard

            number="03"

            icon={

              <HeartPulse size={19} />

            }

            title="Health"

            description="Verify that the deployed service is reachable and healthy."

            accent="pink"

          />



          <FeatureCard

            number="04"

            icon={

              <Check size={19} />

            }

            title="Aggregation"

            description="Combine validation results into one deployment verdict."

            accent="gold"

          />

        </div>

      </section>



      {/* =================================================

          VALIDATION PIPELINE

          ================================================= */}



      <section className="flow-section">

        <div className="section-eyebrow">

          VALIDATION PIPELINE

        </div>



        <h2>

          One deployment.

          <span>

            Every layer checked.

          </span>

        </h2>



        <div className="flow-track">

          <FlowNode

            label="Input"

            icon={

              <Rocket size={17} />

            }

          />



          <FlowLine />



          <FlowNode

            label="Governance"

            icon={

              <ShieldCheck size={17} />

            }

          />



          <FlowLine />



          <FlowNode

            label="Configuration"

            icon={

              <SlidersHorizontal

                size={17}

              />

            }

          />



          <FlowLine />



          <FlowNode

            label="Health"

            icon={

              <HeartPulse size={17} />

            }

          />



          <FlowLine />



          <FlowNode

            label="Aggregator"

            icon={

              <Check size={17} />

            }

          />

        </div>

      </section>

    </div>

  )

}



/* =========================================================

   FLOATING COMMAND HEADER

   ========================================================= */



function CommandHeader() {

  return (

    <header className="command-header glass interactive-surface">

      {/* BRAND */}



      <div className="command-brand">

        <div className="brand-mark">

          <Activity

            size={19}

            strokeWidth={2}

          />

        </div>



        <div>

          <div className="brand-name">

            DeployGuard

          </div>



          <div className="brand-subtitle">

            Deployment Intelligence

          </div>

        </div>

      </div>



      {/* MOVING SYSTEM TICKER */}



      <div className="command-ticker">

        <div className="ticker-track">

          <span>

            DEPLOYMENT SYSTEMS OPERATIONAL

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            GOVERNANCE ENGINE CONNECTED

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            CONFIGURATION VALIDATOR READY

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            HEALTH MONITOR ACTIVE

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            RESULT AGGREGATOR ONLINE

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            DEPLOYMENT INTELLIGENCE ACTIVE

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            VALIDATION PIPELINE READY

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          {/* DUPLICATE SEQUENCE */}



          <span>

            DEPLOYMENT SYSTEMS OPERATIONAL

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            GOVERNANCE ENGINE CONNECTED

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            CONFIGURATION VALIDATOR READY

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            HEALTH MONITOR ACTIVE

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            RESULT AGGREGATOR ONLINE

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            DEPLOYMENT INTELLIGENCE ACTIVE

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>



          <span>

            VALIDATION PIPELINE READY

          </span>



          <i>ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â </i>

        </div>

      </div>



      {/* SYSTEM STATUS */}



      <div className="command-status">

        <span className="status-dot" />



        <span>

          System Online

        </span>

      </div>

    </header>

  )

}



/* =========================================================

   LOADING / CONTEXT TRANSITION

   ========================================================= */



function LoadingScreen({

  currentStep,

  totalSteps,

}: {

  currentStep: number

  totalSteps: number

}) {

  const progress =

    ((currentStep + 1) /

      totalSteps) *

    100



  return (

    <main className="experience-screen loading-screen">

      <div className="loading-container">

        <div className="loading-logo">

          <Activity

            size={28}

            strokeWidth={1.7}

          />

        </div>



        <div className="loading-label">

          DEPLOYGUARD / CONTEXT SWITCH

        </div>



        <h1>

          Reconfiguring your

          <span>

            deployment workspace

          </span>

        </h1>



        <div className="loading-panel glass">

          <div className="loading-panel-header">

            <span>

              SYSTEM INITIALIZATION

            </span>



            <span>

              {Math.round(progress)}%

            </span>

          </div>



          <div className="progress-track">

            <div

              className="progress-fill"

              style={{

                width:

                  `${progress}%`,

              }}

            />

          </div>



          <div className="loading-list">

            {loadingSteps.map(

              (step, index) => {

                const completed =

                  index < currentStep



                const active =

                  index === currentStep



                return (

                  <div

                    key={step}

                    className={`loading-row ${

                      completed

                        ? 'completed'

                        : ''

                    } ${

                      active

                        ? 'active'

                        : ''

                    }`}

                  >

                    <div className="loading-status">

                      {completed ? (

                        <Check size={13} />

                      ) : active ? (

                        <LoaderCircle

                          size={14}

                        />

                      ) : (

                        <span />

                      )}

                    </div>



                    <span>

                      {step}

                    </span>



                    <small>

                      {completed

                        ? 'READY'

                        : active

                          ? 'CONNECTING'

                          : 'WAITING'}

                    </small>

                  </div>

                )

              },

            )}

          </div>

        </div>



        <div className="loading-footer">

          Establishing deployment intelligence

          environment

        </div>

      </div>

    </main>

  )

}



/* =========================================================

   CONTEXT PAGES

   ========================================================= */



function ContextPage({

  page,

  latestDeployment,

  latestValidations,

  onOpenDeployments,

  onDeploymentComplete,

}: {

  page: Exclude<PageName, 'Overview'>

  latestDeployment: Deployment | null

  latestValidations: ValidationResult[]

  onOpenDeployments: () => void

  onDeploymentComplete: (
    deployment: Deployment,
    validations: ValidationResult[],
  ) => void

}) {

  if (page === 'Deployments') {
    return (
      <DeploymentsPage
        latestDeployment={latestDeployment}
        latestValidations={latestValidations}
        onDeploymentComplete={onDeploymentComplete}
      />
    )
  }

  const validationMap = new Map(
    latestValidations.map((item) => [
      item.type,
      item,
    ]),
  )

  const statusClass = (
    status?: string,
  ) =>
    status
      ? `context-status ${status.toLowerCase()}`
      : 'context-status idle'

  const hasDeployment = Boolean(
    latestDeployment,
  )

  const governance = validationMap.get(
    'GOVERNANCE',
  )

  const configuration = validationMap.get(
    'CONFIGURATION',
  )

  const health = validationMap.get(
    'HEALTH',
  )

  const pageInfo: Record<
    Exclude<PageName, 'Overview' | 'Deployments'>,
    {
      eyebrow: string
      title: string
      description: string
      icon: ReactNode
    }
  > = {
    Services: {
      eyebrow: 'SERVICE TOPOLOGY',
      title: 'Your services.',
      description:
        'Inspect the service identity, release version, environment and target used by the latest deployment.',
      icon: <Box size={28} />,
    },
    Governance: {
      eyebrow: 'POLICY VALIDATION',
      title: 'Governance control.',
      description:
        'Inspect the decision returned by the connected governance engine for the latest deployment.',
      icon: <ShieldCheck size={28} />,
    },
    Configuration: {
      eyebrow: 'CONFIGURATION VALIDATION',
      title: 'Configuration intelligence.',
      description:
        'Inspect the configuration checks performed before the deployment received its final verdict.',
      icon: (
        <SlidersHorizontal size={28} />
      ),
    },
    Health: {
      eyebrow: 'SERVICE HEALTH',
      title: 'Health monitoring.',
      description:
        'Inspect the live endpoint check performed against the deployment target.',
      icon: <HeartPulse size={28} />,
    },
    Settings: {
      eyebrow: 'SYSTEM SETTINGS',
      title: 'System configuration.',
      description:
        'View the local services used by DeployGuard and the current runtime data source.',
      icon: <Settings size={28} />,
    },
  }

  const info = pageInfo[
    page as Exclude<
      PageName,
      'Overview' | 'Deployments'
    >
  ]

  const renderValidation = (
    validation: ValidationResult | undefined,
    label: string,
  ) => (
    <div className="glass context-validation-card">
      <div className="context-validation-header">
        <div>
          <span className="panel-eyebrow">
            {label}
          </span>
          <h3>
            {validation?.message ||
              (hasDeployment
                ? 'No validation result returned.'
                : 'Waiting for a deployment.')}
          </h3>
        </div>

        <span
          className={statusClass(
            validation?.status,
          )}
        >
          {validation?.status ?? 'NOT RUN'}
        </span>
      </div>

      {validation?.details && (
        <p className="context-validation-details">
          {typeof validation.details === 'string' ? validation.details : validation.details ? JSON.stringify(validation.details) : ''}
        </p>
      )}

      {!hasDeployment && (
        <p className="context-muted">
          Run a deployment validation to populate
          this panel with live backend data.
        </p>
      )}
    </div>
  )

  return (
    <section className="context-page">
      <CommandHeader />

      <div className="context-content">
        <div className="context-icon glass">
          {info.icon}
        </div>

        <div className="section-eyebrow">
          {info.eyebrow}
        </div>

        <h1>{info.title}</h1>

        <p>{info.description}</p>

        {page === 'Settings' ? (
          <>
            <div className="context-grid settings-grid">
              <div className="glass context-card">
                <span>FRONTEND</span>
                <strong>localhost:5173</strong>
              </div>

              <div className="glass context-card">
                <span>VALIDATION API</span>
                <strong>localhost:8081</strong>
              </div>

              <div className="glass context-card">
                <span>GOVERNANCE ENGINE</span>
                <strong>localhost:8080</strong>
              </div>

              <div className="glass context-card">
                <span>DATA STORE</span>
                <strong>H2 / LOCAL</strong>
              </div>

              <div className="glass context-card">
                <span>DATA SOURCE</span>
                <strong>LIVE BACKEND</strong>
              </div>

              <div className="glass context-card">
                <span>ACTIVE DEPLOYMENT</span>
                <strong>
                  {latestDeployment
                    ? `#${latestDeployment.id}`
                    : 'NONE'}
                </strong>
              </div>
            </div>

            <div className="glass context-validation-card settings-note">
              <div className="context-validation-header">
                <div>
                  <span className="panel-eyebrow">
                    RUNTIME MODEL
                  </span>
                  <h3>
                    Real validation pipeline connected
                  </h3>
                </div>

                <span className="context-status pass">
                  ONLINE
                </span>
              </div>

              <p className="context-validation-details">
                Deployments are submitted to the
                Spring Boot validation API. The API
                orchestrates governance, configuration
                and health checks and persists the
                resulting validation records.
              </p>
            </div>
          </>
        ) : page === 'Services' ? (
          <>
            <div className="context-grid service-grid">
              <div className="glass context-card">
                <span>SERVICE</span>
                <strong>
                  {latestDeployment?.serviceName ??
                    'NO DEPLOYMENT'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>VERSION</span>
                <strong>
                  {latestDeployment
                    ? `v${latestDeployment.version}`
                    : 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>ENVIRONMENT</span>
                <strong>
                  {latestDeployment?.environment ??
                    'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>FINAL STATUS</span>
                <strong>
                  {latestDeployment?.status ??
                    'AWAITING RUN'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>TARGET</span>
                <strong className="context-value-wrap">
                  {latestDeployment?.targetUrl ?? 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>DEPLOYMENT ID</span>
                <strong>
                  {latestDeployment
                    ? `#${latestDeployment.id}`
                    : 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â'}
                </strong>
              </div>
            </div>

            {renderValidation(
              health,
              'LATEST SERVICE HEALTH',
            )}
          </>
        ) : page === 'Governance' ? (
          <>
            <div className="context-grid">
              <div className="glass context-card">
                <span>DECISION</span>
                <strong>
                  {governance?.status ?? 'NOT RUN'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>RULES EVALUATED</span>
                <strong>
                  {(typeof governance?.details === 'string' ? governance.details : '').match(
                    /evaluatedRules=\[([^\]]*)\]/,
                  )?.[1]
                    ? (typeof governance?.details === 'string' ? governance.details : '').match(
                        /evaluatedRules=\[([^\]]*)\]/,
                      )?.[1].split(',').length
                    : '0'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>DEPLOYMENT</span>
                <strong>
                  {latestDeployment
                    ? `#${latestDeployment.id}`
                    : 'NONE'}
                </strong>
              </div>
            </div>

            {renderValidation(
              governance,
              'GOVERNANCE DECISION',
            )}
          </>
        ) : page === 'Configuration' ? (
          <>
            <div className="context-grid">
              <div className="glass context-card">
                <span>SERVICE NAME</span>
                <strong>
                  {latestDeployment?.serviceName
                    ? 'PRESENT'
                    : 'MISSING'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>VERSION</span>
                <strong>
                  {latestDeployment?.version
                    ? 'PRESENT'
                    : 'MISSING'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>ENVIRONMENT</span>
                <strong>
                  {latestDeployment?.environment
                    ? 'PRESENT'
                    : 'MISSING'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>TARGET URL</span>
                <strong>
                  {latestDeployment?.targetUrl
                    ? 'PRESENT'
                    : 'MISSING'}
                </strong>
              </div>
            </div>

            {renderValidation(
              configuration,
              'CONFIGURATION DECISION',
            )}
          </>
        ) : (
          <>
            <div className="context-grid">
              <div className="glass context-card">
                <span>HEALTH RESULT</span>
                <strong>
                  {health?.status ?? 'NOT RUN'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>TARGET</span>
                <strong className="context-value-wrap">
                  {latestDeployment?.targetUrl ?? 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â'}
                </strong>
              </div>

              <div className="glass context-card">
                <span>FINAL STATUS</span>
                <strong>
                  {latestDeployment?.status ??
                    'AWAITING RUN'}
                </strong>
              </div>
            </div>

            {renderValidation(
              health,
              'HEALTH CHECK',
            )}
          </>
        )}

        <button
          className="learn-button magnetic"
          onClick={onOpenDeployments}
        >
          {latestDeployment
            ? 'Run another validation'
            : 'Create your first deployment'}
          <ArrowRight size={15} />
        </button>
      </div>
    </section>
  )
}

function DeploymentsPage({

  latestDeployment,
  latestValidations,
  onDeploymentComplete,

}: {

  latestDeployment: Deployment | null
  latestValidations: ValidationResult[]
  onDeploymentComplete: (
    deployment: Deployment,
    validations: ValidationResult[],
  ) => void

}) {

  const [serviceName, setServiceName] =

    useState('payment-service')



  const [version, setVersion] =

    useState('2.1.0')



  const [environment, setEnvironment] =

    useState('production')



  const [targetUrl, setTargetUrl] =

    useState(

      'http\://localhost:8081',

    )



  const [isSubmitting, setIsSubmitting] =

    useState(false)



  const [deployment, setDeployment] =

    useState<Deployment | null>(

      latestDeployment,

    )



  const [validations, setValidations] =

    useState<ValidationResult[]>(

      latestValidations,

    )



  useEffect(() => {
    setDeployment(latestDeployment)
    setValidations(latestValidations)
  }, [
    latestDeployment,
    latestValidations,
  ])



  const [error, setError] =

    useState<string | null>(null)



  const handleDeploy = async () => {

    setIsSubmitting(true)

    setError(null)

    setDeployment(null)

    setValidations([])



    try {

      const created =

        await createDeployment({

          serviceName,

          version,

          environment,

          targetUrl,

        })



      setDeployment(created)



      const results =

        await getDeploymentValidations(

          created.id,

        )



      setValidations(results)

      onDeploymentComplete(
        created,
        results,
      )

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : 'Unable to create deployment.',

      )

    } finally {

      setIsSubmitting(false)

    }

  }



  return (

    <section className="context-page deployments-page">

      <CommandHeader />



      <div className="deployment-workspace">

        {/* HEADER */}



        <div className="deployment-heading">

          <div>

            <div className="section-eyebrow">

              DEPLOYMENT MONITOR

            </div>



            <h1>

              Validate your

              <span>

                deployment.

              </span>

            </h1>



            <p>

              Submit a deployment and let

              DeployGuard validate governance,

              configuration and service health.

            </p>

          </div>



          <div className="deployment-live-status glass">

            <span className="status-dot" />



            <span>

              VALIDATION ENGINE ONLINE

            </span>

          </div>

        </div>



        {/* MAIN WORKSPACE */}



        <div className="deployment-layout">

          {/* FORM */}



          <div className="deployment-form glass">

            <div className="panel-heading">

              <div>

                <span className="panel-eyebrow">

                  NEW DEPLOYMENT

                </span>



                <h2>

                  Deployment details

                </h2>

              </div>



              <Rocket size={20} />

            </div>



            <div className="deployment-fields">

              <DeploymentField

                label="SERVICE NAME"

                value={serviceName}

                onChange={setServiceName}

                placeholder="payment-service"

              />



              <DeploymentField

                label="VERSION"

                value={version}

                onChange={setVersion}

                placeholder="2.1.0"

              />



              <div className="deployment-field">

                <label>

                  ENVIRONMENT

                </label>



                <select

                  value={environment}

                  onChange={(event) =>

                    setEnvironment(

                      event.target.value,

                    )

                  }

                >

                  <option value="development">

                    development

                  </option>



                  <option value="staging">

                    staging

                  </option>



                  <option value="production">

                    production

                  </option>

                </select>

              </div>



              <DeploymentField

                label="TARGET URL"

                value={targetUrl}

                onChange={setTargetUrl}

                placeholder="http\://localhost:8081"

              />

            </div>



            <button

              className="deployment-submit magnetic"

              onClick={handleDeploy}

              disabled={isSubmitting}

            >

              {isSubmitting ? (

                <>

                  <LoaderCircle

                    size={17}

                    className="spin"

                  />



                  VALIDATING DEPLOYMENT

                </>

              ) : (

                <>

                  <Rocket size={17} />



                  START VALIDATION

                </>

              )}

            </button>



            {error && (

              <div className="deployment-error">

                <span>!</span>



                <div>

                  <strong>

                    Validation request failed

                  </strong>



                  <p>

                    {error}

                  </p>

                </div>

              </div>

            )}

          </div>



          {/* RESULT */}



          <DeploymentResult

            deployment={deployment}

            validations={validations}

            loading={isSubmitting}

          />

        </div>

      </div>

    </section>

  )

}



/* =========================================================

   DEPLOYMENT FIELD

   ========================================================= */



function DeploymentField({

  label,

  value,

  onChange,

  placeholder,

}: {

  label: string

  value: string

  onChange: (value: string) => void

  placeholder: string

}) {

  return (

    <div className="deployment-field">

      <label>

        {label}

      </label>



      <input

        value={value}

        onChange={(event) =>

          onChange(

            event.target.value,

          )

        }

        placeholder={placeholder}

      />

    </div>

  )

}



/* =========================================================

   DEPLOYMENT RESULT

   ========================================================= */



function DeploymentResult({

  deployment,

  validations,

  loading,

}: {

  deployment: Deployment | null

  validations: ValidationResult[]

  loading: boolean

}) {

  if (loading) {

    return (

      <div className="deployment-result glass result-loading">

        <div className="result-orbit">

          <LoaderCircle size={30} />

        </div>



        <span className="panel-eyebrow">

          DEPLOYMENT VALIDATION

        </span>



        <h2>

          Analyzing deployment...

        </h2>



        <p>

          Governance, configuration and

          health checks are being executed.

        </p>



        <div className="validation-preview">

          <ValidationPreviewRow

            label="Governance"

          />



          <ValidationPreviewRow

            label="Configuration"

          />



          <ValidationPreviewRow

            label="Health"

          />

        </div>

      </div>

    )

  }



  if (!deployment) {

    return (

      <div className="deployment-result glass result-empty">

        <div className="result-empty-icon">

          <Rocket size={26} />

        </div>



        <span className="panel-eyebrow">

          VALIDATION RESULT

        </span>



        <h2>

          Ready when you are.

        </h2>



        <p>

          Enter your deployment details and

          start validation to see the real

          backend result here.

        </p>



        <div className="empty-flow">

          <span>INPUT</span>



          <i />



          <span>VALIDATE</span>



          <i />



          <span>RESULT</span>

        </div>

      </div>

    )

  }



  const isSuccess =

    deployment.status === 'SUCCESS'



  return (

    <div className="deployment-result glass result-pop">

      <div

        className={`result-status ${

          isSuccess

            ? 'success'

            : 'failed'

        }`}

      >

        {isSuccess ? (

          <Check size={25} />

        ) : (

          <span>!</span>

        )}

      </div>



      <span className="panel-eyebrow">

        DEPLOYMENT RESULT

      </span>



      <h2>

        {isSuccess

          ? 'Deployment validated.'

          : 'Deployment validation failed.'}

      </h2>



      <p>

        {deployment.serviceName}

        {' . '}
        v{deployment.version}

      </p>



      <div className="result-status-label">

        <span>

          FINAL STATUS

        </span>



        <strong>

          {deployment.status}

        </strong>

      </div>



      <div className="validation-results">

        {validations.map(

          (validation) => (

            <div

              key={validation.id}

              className="validation-result-row"

            >

              <div className="validation-result-icon">

                {validation.status ===

                'PASS' ? (

                  <Check size={14} />

                ) : (

                  <span>!</span>

                )}

              </div>



              <div className="validation-result-content">

                <strong>

                  {validation.type}

                </strong>



                <span>

                  {validation.message ||

                    validation.status}

                </span>



                {validation.details && (

                  <small>

                    {typeof validation.details === 'string' ? validation.details : validation.details ? JSON.stringify(validation.details) : ''}

                  </small>

                )}

              </div>



              <b

                className={`validation-badge ${(validation.status ?? 'SKIPPED').toLowerCase()}`}

              >

                {validation.status}

              </b>

            </div>

          ),

        )}

      </div>



      <div className="result-meta">

        <span>

          Deployment #

          {deployment.id}

        </span>



        <span>

          {deployment.durationMs ?? 0} ms

        </span>

      </div>

    </div>

  )

}



/* =========================================================

   VALIDATION PREVIEW

   ========================================================= */



function ValidationPreviewRow({

  label,

}: {

  label: string

}) {

  return (

    <div className="validation-preview-row">

      <span className="preview-spinner">

        <LoaderCircle size={13} />

      </span>



      <span>

        {label}

      </span>



      <small>

        CHECKING

      </small>

    </div>

  )

}



/* =========================================================

   BACKGROUND

   ========================================================= */



function Background() {
  const backgroundRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const background = backgroundRef.current

    if (!background) {
      return
    }

    let frame = 0
    let targetX = 0
    let targetY = 0
    let currentX = 0
    let currentY = 0

    const handlePointerMove = (event: globalThis.PointerEvent) => {
      targetX =
        (event.clientX / window.innerWidth - 0.5) * 2

      targetY =
        (event.clientY / window.innerHeight - 0.5) * 2
    }

    const animate = () => {
      currentX += (targetX - currentX) * 0.055
      currentY += (targetY - currentY) * 0.055

      background.style.setProperty(
        '--cursor-x',
        `${currentX * 55}px`,
      )

      background.style.setProperty(
        '--cursor-y',
        `${currentY * 55}px`,
      )

      background.style.setProperty(
        '--cursor-nx',
        `${currentX}`,
      )

      background.style.setProperty(
        '--cursor-ny',
        `${currentY}`,
      )

      frame = requestAnimationFrame(animate)
    }

    window.addEventListener('pointermove', handlePointerMove)
    animate()

    return () => {
      window.removeEventListener('pointermove', handlePointerMove)
      cancelAnimationFrame(frame)
    }
  }, [])

  return (
    <div
      ref={backgroundRef}
      className="interactive-background"
    >
      <div className="background-aurora aurora-a" />
      <div className="background-aurora aurora-b" />
      <div className="background-aurora aurora-c" />
      <div className="background-grid" />
      <div className="cursor-glow" />

      <div className="background-particles">
        {Array.from({ length: 28 }).map((_, index) => (
          <span
            key={index}
            style={
              {
                '--particle-index': index,
              } as CSSProperties
            }
          />
        ))}
      </div>
    </div>
  )
}


/* =========================================================
   METRIC
   ========================================================= */

function Metric({

  value,

  label,

}: {

  value: string

  label: string

}) {

  return (

    <div className="metric">

      <strong>

        {value}

      </strong>



      <span>

        {label}

      </span>

    </div>

  )

}



/* =========================================================

   FEATURE CARD

   ========================================================= */



function FeatureCard({

  number,

  icon,

  title,

  description,

  accent,

}: {

  number: string

  icon: ReactNode

  title: string

  description: string

  accent: string

}) {

  const cardRef =

    useRef<HTMLElement>(null)



  const handleMove = (

    event: ReactPointerEvent<HTMLElement>,

  ) => {

    const card =

      cardRef.current



    if (!card) {

      return

    }



    const rect =

      card.getBoundingClientRect()



    const x =

      (

        event.clientX -

        rect.left

      ) /

        rect.width -

      0.5



    const y =

      (

        event.clientY -

        rect.top

      ) /

        rect.height -

      0.5



    card.style.setProperty(

      '--tilt-x',

      `${y * -7}deg`,

    )



    card.style.setProperty(

      '--tilt-y',

      `${x * 9}deg`,

    )



    card.style.setProperty(

      '--spot-x',

      `${(x + 0.5) * 100}%`,

    )



    card.style.setProperty(

      '--spot-y',

      `${(y + 0.5) * 100}%`,

    )

  }



  const reset = () => {

    const card =

      cardRef.current



    if (!card) {

      return

    }



    card.style.setProperty(

      '--tilt-x',

      '0deg',

    )



    card.style.setProperty(

      '--tilt-y',

      '0deg',

    )

  }



  return (

    <article

      ref={cardRef}

      className={`feature-card ${accent}`}

      onPointerMove={handleMove}

      onPointerLeave={reset}

    >

      <div className="feature-top">

        <div className="feature-icon">

          {icon}

        </div>



        <span>

          {number}

        </span>

      </div>



      <h3>

        {title}

      </h3>



      <p>

        {description}

      </p>



      <div className="feature-line" />

    </article>

  )

}



/* =========================================================

   ORBITAL SYSTEM

   ========================================================= */



function OrbitalSystem() {

  const [rotation, setRotation] =

    useState({

      x: 0,

      y: 0,

    })



  const [activeNode, setActiveNode] =

    useState<string | null>(

      null,

    )



  const handleMove = (

    event: ReactPointerEvent<HTMLDivElement>,

  ) => {

    const rect =

      event.currentTarget

        .getBoundingClientRect()



    const normalizedX =

      (

        event.clientX -

        rect.left

      ) /

        rect.width -

      0.5



    const normalizedY =

      (

        event.clientY -

        rect.top

      ) /

        rect.height -

      0.5



    setRotation({

      x:

        normalizedY * -20,



      y:

        normalizedX * 25,

    })

  }



  const resetRotation = () => {

    setRotation({

      x: 0,

      y: 0,

    })

  }



  return (

    <div

      className={`orbital-system ${

        activeNode

          ? 'node-engaged'

          : ''

      }`}

      onPointerMove={

        handleMove

      }

      onPointerLeave={() => {

        resetRotation()

        setActiveNode(null)

      }}

    >

      <div

        className="orbital-stage"

        style={{

          transform: `

            rotateX(${rotation.x}deg)

            rotateY(${rotation.y}deg)

          `,

        }}

      >

        <div className="orbit orbit-outer" />



        <div className="orbit orbit-middle" />



        <div className="orbit orbit-inner" />



        {/* CORE */}



        <div

          className={`orbit-core ${

            activeNode === 'core'

              ? 'core-engaged'

              : ''

          }`}

          onPointerEnter={() =>

            setActiveNode('core')

          }

          onPointerLeave={() =>

            setActiveNode(null)

          }

        >

          <div className="core-energy" />



          <Activity

            size={40}

            strokeWidth={1.3}

          />



          <span>

            VALIDATING

          </span>



          <small>

            DEPLOYMENT CORE

          </small>

        </div>



        {/* GOVERNANCE */}



        <OrbitalNode

          className="governance-node"

          nodeId="governance"

          icon={

            <ShieldCheck size={16} />

          }

          label="GOVERNANCE"

          detail="Policy validation"

          activeNode={activeNode}

          setActiveNode={

            setActiveNode

          }

        />



        {/* CONFIGURATION */}



        <OrbitalNode

          className="config-node"

          nodeId="configuration"

          icon={

            <SlidersHorizontal

              size={16}

            />

          }

          label="CONFIGURATION"

          detail="Environment checks"

          activeNode={activeNode}

          setActiveNode={

            setActiveNode

          }

        />



        {/* HEALTH */}



        <OrbitalNode

          className="health-node"

          nodeId="health"

          icon={

            <HeartPulse size={16} />

          }

          label="HEALTH"

          detail="Service monitoring"

          activeNode={activeNode}

          setActiveNode={

            setActiveNode

          }

        />



        {/* AGGREGATOR */}



        <OrbitalNode

          className="aggregator-node"

          nodeId="aggregator"

          icon={

            <Check size={16} />

          }

          label="AGGREGATOR"

          detail="Final result"

          activeNode={activeNode}

          setActiveNode={

            setActiveNode

          }

        />



        {/* ORBIT PARTICLES */}



        <div className="orbit-particle particle-a" />

        <div className="orbit-particle particle-b" />

        <div className="orbit-particle particle-c" />

        <div className="orbit-particle particle-d" />

        <div className="orbit-particle particle-e" />

        <div className="orbit-particle particle-f" />

      </div>



      <div className="orbital-hint">

        Move your cursor through the system

      </div>

    </div>

  )

}



/* =========================================================

   ORBITAL NODE

   ========================================================= */



function OrbitalNode({

  className,

  nodeId,

  icon,

  label,

  detail,

  activeNode,

  setActiveNode,

}: {

  className: string

  nodeId: string

  icon: ReactNode

  label: string

  detail: string

  activeNode: string | null

  setActiveNode: (

    value: string | null,

  ) => void

}) {

  const active =

    activeNode === nodeId



  return (

    <div

      className={`

        orbital-node

        ${className}

        ${active ? 'node-active' : ''}

      `}

      onPointerEnter={() =>

        setActiveNode(nodeId)

      }

      onPointerLeave={() =>

        setActiveNode(null)

      }

    >

      <div className="node-icon">

        {icon}

      </div>



      <div className="node-info">

        <strong>

          {label}

        </strong>



        <span>

          {detail}

        </span>

      </div>



      <div className="node-signal" />

    </div>

  )

}



/* =========================================================

   FLOW NODE

   ========================================================= */



function FlowNode({

  label,

  icon,

}: {

  label: string

  icon: ReactNode

}) {

  return (

    <div className="flow-node glass">

      <div className="flow-icon">

        {icon}

      </div>



      <span>

        {label}

      </span>



      <div className="flow-energy" />

    </div>

  )

}



/* =========================================================

   FLOW CONNECTION

   ========================================================= */



function FlowLine() {

  return (

    <div className="flow-line">

      <span />



      <i />



      <i />



      <i />

    </div>

  )

}



/* =========================================================

   EXPORT

   ========================================================= */



export default App