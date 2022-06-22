import React from 'react';
import cn from 'classnames';
import SVG from 'UI/SVG';
import styles from './icon.module.css';

const Icon = ({
  name,
  size = 12,
  height = size,
  width = size,
  color = 'gray-medium',
  className = '',
  style={},
  marginRight = 0,
  inline = false,
  ...props
}) => {
  const _style = {
    width: `${ width }px`,
    height: `${ height }px`,
    ...style,
  };
  if (marginRight){
    _style.marginRight = `${ marginRight }px`;
  }

  const additionalStyles = color === 'inherit' ? { fill: 'currentcolor' } : {}

  return (
    <span
      { ...props }
      style={{..._style, ...additionalStyles }}
      className={ cn(className, styles.wrapper, `fill-${ color }`) }
      data-inline={ inline }
    >
      <SVG name={ name } height={ height } width={ width } />
    </span>
  );
}

Icon.displayName = 'Icon';
export default Icon;
