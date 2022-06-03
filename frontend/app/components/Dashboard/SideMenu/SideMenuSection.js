import { SideMenuitem } from 'UI';
import SideMenuHeader from './SideMenuHeader';
import { setShowAlerts } from 'Duck/dashboard';
import stl from './sideMenuSection.module.css';
import { connect } from 'react-redux';
import { NavLink } from 'react-router-dom';
import { withSiteId } from 'App/routes';
import CustomMetrics from 'Shared/CustomMetrics';

function SideMenuSection({ title, items, onItemClick, setShowAlerts, siteId, activeSection }) {
	return (
		<>
			<SideMenuHeader className="mb-4" text={ title }/>
		  { items.filter(i => i.section === 'metrics').map(item =>
		      <SideMenuitem
		      	key={ item.key }
		        active={ item.active }
		        title={ item.label }
		        iconName={ item.icon }
		        onClick={() => onItemClick(item)}
		      />
		  )}

			<div className={stl.divider} />
			<div className="my-3">
				<SideMenuitem
					id="menu-manage-alerts"
					title="Manage Alerts"
					iconName="bell-plus"
					onClick={() => setShowAlerts(true)}
				/>
			</div>
			<div className={stl.divider} />
			<div className="my-3">
				<CustomMetrics />
			</div>
		</>
	);
}

SideMenuSection.displayName = "SideMenuSection";

export default connect(state => ({
	siteId: state.getIn([ 'site', 'siteId' ])
}), { setShowAlerts })(SideMenuSection);
