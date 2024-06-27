import React from 'react'

function ExCard({
                    title,
                    children,
                    type,
                    onCard,
                    height,
                }: {
    title: React.ReactNode;
    children: React.ReactNode;
    type: string;
    onCard: (card: string) => void;
    height?: number;
}) {
    console.log(type)
    return (
        <div
            className={'rounded-lg overflow-hidden border border-transparent p-4 bg-white hover:border-blue hover:shadow-sm relative'}
            style={{width: '100%', height: height || 286}}
        >
            <div className={'font-medium text-lg'}>{title}</div>
            <div className={'flex flex-col gap-2 mt-2 cursor-pointer'}
                 style={{height: height ? height - 50 : 236}}
                 onClick={() => onCard(type)}>{children}</div>
        </div>
    );
}

export default ExCard
