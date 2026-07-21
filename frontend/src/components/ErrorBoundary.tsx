import {Component,type ErrorInfo,type ReactNode} from 'react'

type Props={children:ReactNode}
type State={error:Error|null;resetKey:number}

export class ErrorBoundary extends Component<Props,State>{
 state:State={error:null,resetKey:0}

 static getDerivedStateFromError(error:Error):Partial<State>{
  return {error}
 }

 componentDidCatch(error:Error,info:ErrorInfo){
  console.error('ANVAYA render error',error,info)
 }

 retry=()=>{
  this.setState(state=>({error:null,resetKey:state.resetKey+1}))
 }

 render(){
  if(this.state.error){
   return <main className="mx-auto flex min-h-screen max-w-xl items-center px-5">
    <section role="alert" className="w-full rounded-2xl border border-red-200 bg-white p-6 shadow-panel">
     <p className="text-xs font-bold uppercase tracking-wide text-red-700">Prototype recovery</p>
     <h1 className="mt-2 text-xl font-semibold text-navy-950">This view could not be displayed.</h1>
     <p className="mt-2 text-sm text-slate-600">Your browser session is still open. Retry the view; if the problem continues, start a new chat.</p>
     <button type="button" onClick={this.retry} className="mt-4 rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800">Retry</button>
    </section>
   </main>
  }
  return <div key={this.state.resetKey}>{this.props.children}</div>
 }
}
