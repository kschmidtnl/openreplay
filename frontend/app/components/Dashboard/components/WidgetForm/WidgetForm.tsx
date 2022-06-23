import React, { useState } from 'react';
import { metricTypes, metricOf, issueOptions } from 'App/constants/filterOptions';
import { FilterKey } from 'Types/filter/filterType';
import { useStore } from 'App/mstore';
import { useObserver } from 'mobx-react-lite';
import { Button, Icon } from 'UI'
import FilterSeries from '../FilterSeries';
import { confirm } from 'UI';
import Select from 'Shared/Select'
import { withSiteId, dashboardMetricDetails, metricDetails } from 'App/routes'
import DashboardSelectionModal from '../DashboardSelectionModal/DashboardSelectionModal';

interface Props {
    history: any;
    match: any;
    onDelete: () => void;
}

function WidgetForm(props: Props) {
    const [showDashboardSelectionModal, setShowDashboardSelectionModal] = useState(false);
    const { history, match: { params: { siteId, dashboardId, metricId } } } = props;
    const { metricStore, dashboardStore } = useStore();
    const dashboards = dashboardStore.dashboards;
    const isSaving = useObserver(() => metricStore.isSaving);
    const metric: any = useObserver(() => metricStore.instance)

    const timeseriesOptions = metricOf.filter(i => i.type === 'timeseries');
    const tableOptions = metricOf.filter(i => i.type === 'table');
    const isTable = metric.metricType === 'table';
    const isFunnel = metric.metricType === 'funnel';
    const canAddToDashboard = metric.exists() && dashboards.length > 0;
    const canAddSeries = metric.series.length < 3;

    // const write = ({ target: { value, name } }) => metricStore.merge({ [ name ]: value });
    const writeOption = ({ value, name }: any) => {
        value = Array.isArray(value) ? value : value.value
        const obj: any = { [ name ]: value };

        if (name === 'metricValue') {
            obj['metricValue'] = value;

            // handle issues (remove all when other option is selected)
            if (Array.isArray(obj['metricValue']) && obj['metricValue'].length > 1) {
                obj['metricValue'] = obj['metricValue'].filter(i => i.value !== 'all');
            }
        }

        if (name === 'metricOf') {
            // if (value === FilterKey.ISSUE) {
            //     obj['metricValue'] = [{ value: 'all', label: 'All' }];
            // }
        }

        if (name === 'metricType') {
            if (value === 'timeseries') {
                obj['metricOf'] = timeseriesOptions[0].value;
                obj['viewType'] = 'lineChart';
            } else if (value === 'table') {
                obj['metricOf'] = tableOptions[0].value;
                obj['viewType'] = 'table';
            }
        }

        metricStore.merge(obj);
    };

    const onSave = () => {
        const wasCreating = !metric.exists()
        metricStore.save(metric, dashboardId)
            .then((metric: any) => {
                if (wasCreating) {
                    if (parseInt(dashboardId) > 0) {
                        history.replace(withSiteId(dashboardMetricDetails(parseInt(dashboardId), metric.metricId), siteId));
                    } else {
                        history.replace(withSiteId(metricDetails(metric.metricId), siteId));
                    }
                }
            });
    }

    const onDelete = async () => {
        if (await confirm({
          header: 'Confirm',
          confirmButton: 'Yes, delete',
          confirmation: `Are you sure you want to permanently delete this metric?`
        })) {
            metricStore.delete(metric).then(props.onDelete);
        }
    }

    const onObserveChanges = () => {
        // metricStore.fetchMetricChartData(metric);
    }

    return useObserver(() => (
        <div className="p-6">
            <div className="form-group">
                <label className="font-medium">Metric Type</label>
                <div className="flex items-center">
                    <Select
                        name="metricType"
                        options={metricTypes}
                        value={metricTypes.find((i: any) => i.value === metric.metricType) || metricTypes[0]}
                        onChange={ writeOption }
                    />

                    {metric.metricType === 'timeseries' && (
                        <>
                            <span className="mx-3">of</span>
                            <Select
                                name="metricOf"
                                options={timeseriesOptions}
                                defaultValue={metric.metricOf}
                                onChange={ writeOption }
                            />
                        </>
                    )}

                    {metric.metricType === 'table' && (
                        <>
                            <span className="mx-3">of</span>
                            <Select
                                name="metricOf"
                                options={tableOptions}
                                defaultValue={metric.metricOf}
                                onChange={ writeOption }
                            />
                        </>
                    )}

                    {metric.metricOf === FilterKey.ISSUE && (
                        <>
                            <span className="mx-3">issue type</span>
                            <Select
                                name="metricValue"
                                options={issueOptions}
                                value={metric.metricValue}
                                onChange={ writeOption }
                                isMulti={true}
                                placeholder="All Issues"
                            />
                        </>
                    )}

                    {metric.metricType === 'table' && !(metric.metricOf === FilterKey.ERRORS || metric.metricOf === FilterKey.SESSIONS) && (
                    <>
                        <span className="mx-3">showing</span>
                        <Select
                            name="metricFormat"
                            options={[
                                { value: 'sessionCount', label: 'Session Count' },
                            ]}
                            defaultValue={ metric.metricFormat }
                            onChange={ writeOption }
                        />
                    </>
                    )}
                </div>
            </div>

            <div className="form-group">
                <div className="flex items-center font-medium py-2">
                    {`${(isTable || isFunnel) ? 'Filter by' : 'Chart Series'}`}
                    {!isTable && !isFunnel && (
                        <Button
                            className="ml-2"
                            variant="text-primary"
                            onClick={() => metric.addSeries()}
                            disabled={!canAddSeries}
                        >Add Series</Button>
                    )}
                </div>

                {metric.series.length > 0 && metric.series.slice(0, (isTable || isFunnel) ? 1 : metric.series.length).map((series: any, index: number) => (
                    <div className="mb-2">
                        <FilterSeries
                            hideHeader={ isTable }
                            seriesIndex={index}
                            series={series}
                            // onRemoveSeries={() => removeSeries(index)}
                            onRemoveSeries={() => metric.removeSeries(index)}
                            canDelete={metric.series.length > 1}
                            emptyMessage={isTable ?
                                'Filter data using any event or attribute. Use Add Step button below to do so.' :
                                'Add user event or filter to define the series by clicking Add Step.'
                            }
                            // observeChanges={onObserveChanges}
                        />
                    </div>
                ))}
            </div>

            <div className="form-groups flex items-center justify-between">
                <Button
                    variant="primary"
                    onClick={onSave}
                    disabled={isSaving}
                >
                    {metric.exists() ? 'Update' : 'Create'}
                </Button>
                <div className="flex items-center">
                    {metric.exists() && (
                        <>
                            <Button variant="text-primary" onClick={onDelete}>
                                <Icon name="trash" size="14" className="mr-2" color="teal"/>
                                Delete
                            </Button>
                            <Button
                                variant="text-primary"
                                className="ml-2"
                                onClick={() => setShowDashboardSelectionModal(true)}
                                disabled={!canAddToDashboard}
                            >
                                <Icon name="columns-gap" size="14" className="mr-2" color="teal"/>
                                Add to Dashboard
                            </Button>
                        </>
                    )}
                </div>
            </div>
            { canAddToDashboard && (
                <DashboardSelectionModal
                    metricId={metric.metricId}
                    show={showDashboardSelectionModal}
                    closeHandler={() => setShowDashboardSelectionModal(false)}
                />
            )}
        </div>
    ));
}

export default WidgetForm;
